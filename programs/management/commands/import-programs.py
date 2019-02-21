from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from programs.models import *

import urllib2
import json
from tabulate import tabulate

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
    programs_processed = 0
    programs_added = 0
    programs_deactivated = 0
    programs_updated = 0
    colleges_added = 0
    departments_added = 0
    # Refers to colleges being removed from a program
    colleges_changed = 0
    # Refers to departments being removed from a program
    departments_changed = 0
    # A collection of program ids added or updated
    programs = []
    # A list of programs deactived
    deactivated_programs = []

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

        self.deactivate_stale_programs()
        self.print_results()

        return 0

    def add_program(self, data):
        program = None
        self.programs_processed += 1

        # Correct college name issue
        data['College_Full'] = self.common_replace(data['College_Full'])

        try:
            program = Program.objects.get(plan_code=data['Plan'], subplan_code__isnull=True)
            program.name = unidecode(data['PlanName'])
            self.programs_updated += 1
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['PlanName']),
                plan_code=data['Plan']
            )
            self.programs_added += 1

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

        self.programs.append(program.id)

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

        college_removed = False

        # Remove non-primary colleges
        for c in program.colleges.all():
            if c.short_name != college.short_name:
                program.colleges.remove(c)
                if college_removed == False:
                    college_removed = True


        if college_removed:
            self.colleges_changed += 1

        # Handle Departments
        department, create = Department.objects.get_or_create(
            full_name=data['Dept_Full']
        )

        if "school" in department.full_name.lower():
            department.school = True
            department.save()

        program.departments.add(department)

        department_removed = False

        for d in program.departments.all():
            if d.full_name != department.full_name:
                program.departments.remove(d)
                if department_removed == False:
                    department_removed = True

        if department_removed:
            self.departments_changed += 1

        program.save()

        return program

    def add_subplan(self, data, parent):
        program = None
        self.programs_processed += 1

        try:
            program = Program.objects.get(
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'])

            program.name = unidecode(data['Subplan_Name'])
            self.programs_updated += 1
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['Subplan_Name']),
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'],
                parent_program=parent
            )
            self.programs_added += 1

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

        self.programs.append(program.id)

        # Handle Colleges and Departments
        for college in parent.colleges.all():
            program.colleges.add(college)

        college_removed = False

        # Remove non-primary colleges
        for college in program.colleges.exclude(pk__in=parent.colleges.all().values_list('pk', flat=True)):
            program.colleges.remove(college)
            college_removed = True

        if college_removed:
            self.colleges_changed += 1

        for department in parent.departments.all():
            program.departments.add(department)

        department_removed = False

        # Remove non-primary departments
        for department in program.departments.exclude(pk__in=parent.departments.all().values_list('pk', flat=True)):
            program.departments.remove(department)
            department_removed = True

        if department_removed:
            self.departments_changed += 1

        program.save()

    def common_replace(self, input):
        return input.replace('&', 'and')

    def deactivate_stale_programs(self):
        """
        Deactivate all programs not processed during the import
        """
        all_programs = Program.objects.all().values_list('id', flat=True)

        for program in self.programs:
            if program not in all_programs:
                p = Program.objects.get(id=program)
                p.active = False
                p.save()
                self.deactivated_programs.append(p.pk)
                self.programs_deactivated += 1

    def print_results(self):
        """
        Prints the results of the import to the stdout
        """
        results = [
            ('Programs Processed', self.programs_processed),
            ('Programs Created', self.programs_added),
            ('Programs Updated', self.programs_updated),
            ('Programs Deactivated', self.programs_deactivated)
        ]
        relationships = [
            ('Programs with college change', self.colleges_changed),
            ('Programs with department change', self.departments_changed),
        ]
        taxonomies = [
            ('Colleges Created', self.colleges_added),
            ('Departments Created', self.departments_added)
        ]

        self.stdout.write('''
Import Complete!

        ''')

        self.stdout.write(tabulate(results, tablefmt='grid'), ending='\n\n')
        self.stdout.write(tabulate(relationships, tablefmt='grid'), ending='\n\n')
        self.stdout.write(tabulate(taxonomies, tablefmt='grid'), ending='\n\n')

        if len(self.deactivated_programs) > 0:
            row_headers = ["Name", "Level", "Degree", "Career"]
            programs = Program.objects.filter(pk__in=self.deactivated_programs).values_list('name', 'level__name', 'degree__name', 'career__name')
            self.stdout.write(tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write("There were no programs deactivated.", ending='\n\n')
