import csv

from django.core.management.base import BaseCommand

from units.models import College
from units.models import Department
from units.models import Division
from units.models import Organization

from programs.models import College as ProgramCollege
from programs.models import Department as ProgramDepartment


class Command(BaseCommand):
    help = 'Sanitizes external organization, division, college and department names'

    fieldnames = [
        'unit_type',
        'ext_id',
        'ext_name',
        'programs_mapping',
        'sanitized_name'
    ]

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            'csv',
            type=str,
            help='A CSV file with a list of units, desired sanitized names, and names of objects that should be mapped to in Programs.'
        )

        parser.add_argument(
            '--skip-first-row',
            action='store_true',
            dest='skip_first',
            help='Skips the first row of the CSV.',
            default=False
        )

        parser.add_argument(
            '--do-not-associate',
            action='store_false',
            dest='associate_units',
            help='Skips the process of associating data throughout the app back to unit records',
            default=True
        )

    def handle(self, *args, **options):
        self.filepath = options['csv']
        self.skip_first = options['skip_first']
        self.associate_units = options['associate_units']

        self.departments_data = {}
        self.organizations_data = {}
        self.divisions_data = {}
        self.colleges_data = {}
        self.process_csv()

        self.colleges_processed = College.objects.all()
        self.organizations_processed = Organization.objects.all()
        self.divisions_processed = Division.objects.all()
        self.departments_processed = Department.objects.all()

        self.colleges_updated = 0
        self.organizations_updated = 0
        self.divisions_updated = 0
        self.departments_updated = 0
        self.colleges_matched = 0
        self.departments_matched = 0

        self.sanitize_college_names()
        self.sanitize_organization_names()
        self.sanitize_division_names()
        self.sanitize_department_names()

        self.print_stats()


    def process_csv(self):
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f, fieldnames=self.fieldnames)

            if self.skip_first:
                next(reader)

            for row in reader:
                unit_type = row['unit_type'].strip().lower()
                ext_id = row['ext_id'].strip()
                ext_name = row['ext_name'].strip()
                programs_mapping = row['programs_mapping'].strip()
                sanitized_name = row['sanitized_name'].strip()

                if unit_type == 'department':
                    if ext_id in self.departments_data.keys():
                        if programs_mapping:
                            self.departments_data[ext_id]['programs_mapping'].append(programs_mapping)
                    else:
                        self.departments_data[ext_id] = {
                            'programs_mapping': [programs_mapping] if programs_mapping else [],
                            'sanitized_name': sanitized_name
                        }
                elif unit_type == 'organization':
                    self.organizations_data[ext_id] = {
                        'sanitized_name': sanitized_name
                    }
                elif unit_type == 'division':
                    self.divisions_data[ext_name] = {
                        'sanitized_name': sanitized_name
                    }
                elif unit_type == 'college':
                    if ext_name in self.colleges_data.keys():
                        if programs_mapping:
                            self.colleges_data[ext_name]['programs_mapping'].append(programs_mapping)
                    else:
                        self.colleges_data[ext_name] = {
                            'programs_mapping': [programs_mapping] if programs_mapping else [],
                            'sanitized_name': sanitized_name
                        }


    def sanitize_college_names(self):
        for college in self.colleges_processed:
            try:
                college_data = self.colleges_data[college.ext_college_name]
            except KeyError:
                continue

            college.sanitized_name = college_data['sanitized_name']
            college.save()
            self.colleges_updated += 1

            if self.associate_units:
                for program_mapping in college_data['programs_mapping']:
                    try:
                        match = ProgramCollege.objects.get(full_name=program_mapping)
                        match.unit_college = college
                        match.save()

                        self.colleges_matched += 1
                    except ProgramCollege.DoesNotExist:
                        pass


    def sanitize_organization_names(self):
        for org in self.organizations_processed:
            try:
                org_data = self.organizations_data[org.ext_org_id]
            except KeyError:
                continue

            org.sanitized_name = org_data['sanitized_name']
            org.save()
            self.organizations_updated += 1


    def sanitize_division_names(self):
        for division in self.divisions_processed:
            try:
                division_data = self.divisions_data[division.ext_division_name]
            except KeyError:
                continue

            division.sanitized_name = division_data['sanitized_name']
            division.save()
            self.divisions_updated += 1


    def sanitize_department_names(self):
        for dept in self.departments_processed:
            try:
                dept_data = self.departments_data[dept.ext_department_id]
            except KeyError:
                continue

            dept.sanitized_name = dept_data['sanitized_name']
            dept.save()
            self.departments_updated += 1

            if self.associate_units:
                for program_mapping in dept_data['programs_mapping']:
                    try:
                        match = ProgramDepartment.objects.get(full_name=program_mapping)
                        match.unit_department = dept
                        match.save()

                        self.departments_matched += 1
                    except ProgramDepartment.DoesNotExist:
                        pass


    def print_stats(self):
        msg = f"""
Colleges Updated      : {self.colleges_updated}/{self.colleges_processed.count()}
Organizations Updated : {self.organizations_updated}/{self.organizations_processed.count()}
Divisions Updated     : {self.divisions_updated}/{self.divisions_processed.count()}
Departments Updated   : {self.departments_updated}/{self.departments_processed.count()}

Program Data Matching
-----------------------
Colleges Associated    : {self.colleges_matched}/{self.colleges_processed.count()}
Departments Associated : {self.departments_matched}/{self.departments_processed.count()}
        """

        self.stdout.write(self.style.SUCCESS(msg))
