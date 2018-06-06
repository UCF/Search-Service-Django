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

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The url of the APIM API.')
        parser.add_argument(
            '--mapping-path',
            type=file,
            dest='mapping_path',
            help='The filepath of the mapping file.',
            required=False
        )

    def handle(self, *args, **options):
        new_modified_date = timezone.now()
        path = options['path']
        mapping_path = options['mapping_path']
        response = urllib2.urlopen(path)

        if mapping_path:
            self.mappings = json.loads(mapping_path.read())

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

        if data['Meta Data'][0]['UCFOnline'] == "1":
            program.online = True

        program.save()

        # Handle Colleges and Departments
        for college in parent.colleges.all():
            program.colleges.add(college)

        for department in parent.departments.all():
            program.departments.add(department)

        program.save()
