import csv

from django.core.management.base import BaseCommand
from argparse import FileType

from units.models import College
from units.models import Department
from units.models import Division
from units.models import Employee
from units.models import Organization


class Command(BaseCommand):
    help = 'Imports a CSV of employees and their associated units.'

    fieldnames = [
        'Employee ID',
        'Full Name',
        'First Name',
        'Last Name',
        'Prefix',
        'Dept ID',
        'Department Descr',
        'VP Org',
        'VP Org Descr',
        'Division',
        'College'
    ]

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            'csv',
            type=str,
            help='The CSV file with a list of employees and associated units'
        )

        parser.add_argument(
            '--skip-first-row',
            action='store_true',
            dest='skip_first',
            help='Skips the first row of the CSV.',
            default=False
        )

    def handle(self, *args, **options):
        self.filepath = options['csv']
        self.skip_first = options['skip_first']

        self.employees_processed = 0
        self.employees_created = 0
        self.employees_updated = 0

        self.departments_created = 0
        self.organizations_created = 0
        self.divisions_created = 0
        self.colleges_created = 0

        self.import_employees()
        self.print_stats()

    def import_employees(self):
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f, fieldnames=self.fieldnames)

            if self.skip_first:
                next(reader)

            for row in reader:
                self.employees_processed += 1

                dept_id = row['Dept ID'].strip()
                dept_name = row['Department Descr'].strip()
                org_id = row['VP Org'].strip()
                org_name = row['VP Org Descr'].strip()
                division_name = row['Division'].strip()
                college_name = row['College'].strip()

                department = None
                organization = None
                division = None
                college = None

                # Get or create the department
                try:
                    department = Department.objects.get(ext_department_id=dept_id)
                except Department.DoesNotExist:
                    department = Department(
                        ext_department_id=dept_id,
                        ext_department_name=dept_name
                    )
                    department.save()
                    self.departments_created += 1


                # Get or create the organization
                try:
                    organization = Organization.objects.get(ext_org_id=org_id)
                except Organization.DoesNotExist:
                    organization = Organization(
                        ext_org_id=org_id,
                        ext_org_name=org_name
                    )
                    organization.save()
                    self.organizations_created += 1

                # Get or create the division
                if division_name:
                    try:
                        division = Division.objects.get(ext_division_name=division_name)
                    except Division.DoesNotExist:
                        division = Division(
                            ext_division_name=division_name
                        )
                        division.save()
                        self.divisions_created += 1

                # Get or create the college
                if college_name:
                    try:
                        college = College.objects.get(ext_college_name=college_name)
                    except College.DoesNotExist:
                        college = College(
                            ext_college_name=college_name
                        )
                        college.save()
                        self.colleges_created += 1

                empl_id = row['Employee ID']

                try:
                    existing_employee = Employee.objects.get(ext_employee_id=empl_id)
                    existing_employee.full_name = row['Full Name'].strip()
                    existing_employee.first_name = row['First Name'].strip()
                    existing_employee.last_name = row['Last Name'].strip()
                    existing_employee.prefix = row['Prefix'].strip() if row['Prefix'].strip() != '' else None
                    existing_employee.department = department
                    existing_employee.organization = organization
                    existing_employee.division = division
                    existing_employee.college = college
                    existing_employee.save()
                    self.employees_updated += 1

                except Employee.DoesNotExist:
                    new_employee = Employee(
                        ext_employee_id=empl_id,
                        full_name=row['Full Name'].strip(),
                        first_name=row['First Name'].strip(),
                        last_name=row['Last Name'].strip(),
                        prefix=row['Prefix'].strip() if row['Prefix'].strip() != '' else None,
                        department=department,
                        organization=organization,
                        division=division,
                        college=college
                    )

                    new_employee.save()
                    self.employees_created += 1

    def print_stats(self):
        msg = f"""
Employees Processed   : {self.employees_processed}
Employees Created     : {self.employees_created}
Employees Updated     : {self.employees_updated}

Departments Created   : {self.departments_created}
Organizations Created : {self.organizations_created}
Divisions Created     : {self.divisions_created}
Colleges Created      : {self.colleges_created}
        """

        self.stdout.write(self.style.SUCCESS(msg))
