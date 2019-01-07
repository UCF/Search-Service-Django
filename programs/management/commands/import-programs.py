from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from programs.models import *

import urllib2
import json

from unidecode import unidecode


class Command(BaseCommand):
    help = 'Imports programs from the Academic Programs Inventory Master.'
    career_mappings = {
        "UGRD": "Undergraduate",
        "GRAD": "Graduate",
        "PROF": "Professional"
    }
    mappings = {}
    use_internal_mapping = False

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The url of the APIM API.')

        parser.add_argument(
            '--mapping-path',
            type=str,
            dest='mapping_path',
            help='The url of the mapping file.',
            required=False
        )

        parser.add_argument(
            '--use-internal-mapping',
            type=bool,
            dest='use_internal_mapping',
            help='Will use the college mappings within the search service data.',
            required=False
        )

    def handle(self, *args, **options):
        new_modified_date = timezone.now()
        path = options['path']
        mapping_path = options['mapping_path']
        self.use_internal_mapping = options['use_internal_mapping']
        response = urllib2.urlopen(path)

        if mapping_path and not self.use_internal_mapping:
            mapping_resp = urllib2.urlopen(mapping_path)
            self.mappings = json.loads(mapping_resp.read())
        elif self.use_internal_mapping:
            self.mappings = CollegeOverride.objects.all()
        else:
            self.mappings = None

        data = json.loads(response.read())

        # Create/update programs from feed data
        for d in data:
            # Ignore pending and non-degree programs
            if d['Meta Data'][0]['Degree'] in ['PND', 'PRP']:
                continue

            program = self.add_program(d)

            if len(d['SubPlans']) > 0:
                for sp in d['SubPlans']:
                    self.add_subplan(sp, program)

        # Remove stale programs
        Program.objects.filter(modified__lt=new_modified_date).delete()

        return 0

    def add_program(self, data):
        program = None

        # Correct college name issue
        data['College_Full'] = self.common_replace(data['College_Full'])

        try:
            program = Program.objects.get(plan_code=data['Plan'], subplan_code__isnull=True)
            program.name = unidecode(data['PlanName'])
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['PlanName']),
                plan_code=data['Plan']
            )

        # Handle Career
        career = self.career_mappings[data['Career']]
        career, created = Career.objects.get_or_create(
            name=career, abbr=data['Career']
        )

        program.career = career

        # Handle degree
        degree, created = Degree.objects.get_or_create(
            name=data['Meta Data'][0]['Degree']
        )

        program.degree = degree

        # Handle level
        temp_level = 'None'
        if data['Level'] == '':
            if degree.name in ['CER', 'CRT']:
                temp_level = 'Certificate'
            if degree.name == 'MIN':
                temp_level = 'Minor'
        else:
            temp_level = data['Level']

        level, created = Level.objects.get_or_create(name=temp_level)

        program.level = level

        if data['Meta Data'][0]['UCFOnline'] == "1":
            program.online = True

        program.save()

        mapping = None

        if self.mappings:
            if self.use_internal_mapping:
                try:
                    mapping = self.mappings.filter(plan_code=data['Plan'], subplan_code=None)
                except:
                    mapping = None
            else:
                mapping = [x for x in self.mappings['programs'] if x['plan_code'] == data['Plan'] and x['subplan_code'] == None]

        if mapping:
            if self.use_internal_mapping:
                mapping = mapping[0]
                data['College_Full'] = mapping.college.full_name
                data['CollegeShort'] = mapping.college.short_name
            else:
                mapping = mapping[0]
                data['College_Full'] = mapping['college']['name']
                data['CollegeShort'] = mapping['college']['short_name']


        # Handle Colleges
        college, create = College.objects.get_or_create(
            full_name=data['College_Full'],
            short_name=data['CollegeShort']
        )

        program.colleges.add(college)

        # Handle Departments
        department, create = Department.objects.get_or_create(
            full_name=data['Dept_Full']
        )

        if "school" in department.full_name.lower():
            department.school = True
            department.save()

        program.departments.add(department)

        program.save()

        return program

    def add_subplan(self, data, parent):
        program = None

        try:
            program = Program.objects.get(
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'])

            program.name = unidecode(data['Subplan_Name'])
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['Subplan_Name']),
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'],
                parent_program=parent
            )

        # Handle Career and Level

        program.career = parent.career
        program.level = parent.level

        # Handle degree
        degree, created = Degree.objects.get_or_create(
            name=data['Meta Data'][0]['Degree']
        )

        program.degree = degree

        if data['Meta Data'][0]['UCFOnline'] == "1" or data['Subplan'].startswith('Z'):
            program.online = True

        program.save()

        # Handle Colleges and Departments
        for college in parent.colleges.all():
            program.colleges.add(college)

        for department in parent.departments.all():
            program.departments.add(department)

        program.save()

    def common_replace(self, input):
        return input.replace('&', 'and')
