from django.core.management.base import BaseCommand, CommandError

from units.models import College
from units.models import Department
from units.models import Division
from units.models import Organization
from units.utils import Utilities

from programs.models import College as ProgramCollege
from programs.models import Department as ProgramDepartment

class Command(BaseCommand):
    help = 'Sanitizes external organization, division, college and department names'

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--do-not-associate',
            action='store_false',
            dest='associate_units',
            help='Skips the process of associating data throughout the app back to unit records',
            default=True
        )

    def handle(self, *args, **options):
        self.associate_units = options['associate_units']

        self.colleges_processed = College.objects.all()
        self.orgs_processed = Organization.objects.all()
        self.divisions_processed = Division.objects.all()
        self.departments_processed = Department.objects.all()

        self.colleges_matched = 0
        self.departments_matched = 0

        self.sanitize_college_names()
        self.sanitize_org_names()
        self.sanitize_division_names()
        self.sanitize_department_names()

        self.print_stats()

    def sanitize_college_names(self):
        for college in self.colleges_processed:
            sanitized_name = Utilities.sanitize_unit_name(college.ext_college_name)
            college.sanitized_name = sanitized_name
            college.save()

            if self.associate_units:
                self.associate_college(college)

    def sanitize_org_names(self):
        for org in self.orgs_processed:
            sanitized_name = Utilities.sanitize_unit_name(org.ext_org_name)
            org.sanitized_name = sanitized_name
            org.save()

    def sanitize_division_names(self):
        for division in self.divisions_processed:
            sanitized_name = Utilities.sanitize_unit_name(division.ext_division_name)
            division.sanitized_name = sanitized_name
            division.save()

    def sanitize_department_names(self):
        for department in self.departments_processed:
            sanitized_name = Utilities.sanitize_unit_name(department.ext_department_name)
            department.sanitized_name = sanitized_name
            department.save()

            if self.associate_units:
                self.associate_department(department)

    def associate_college(self, college):
        try:
            match = ProgramCollege.objects.get(full_name=college.name)
            match.unit_college = college;
            match.save()
            self.colleges_matched += 1
        except:
            pass

    def associate_department(self, department):
        try:
            match = ProgramDepartment.objects.get(full_name=department.name)
            match.unit_department = department
            match.save()
            self.departments_matched += 1
        except:
            pass

    def print_stats(self):
        msg = f"""
Colleges Updated      : {self.colleges_processed.count()}
Organizations Updated : {self.orgs_processed.count()}
Divisions Updated     : {self.divisions_processed.count()}
Departments Updated   : {self.departments_processed.count()}

Program Data Matching
-----------------------
Colleges Associated    : {self.colleges_matched}/{self.colleges_processed.count()}
Departments Associated : {self.departments_matched}/{self.departments_processed.count()}
        """

        self.stdout.write(self.style.SUCCESS(msg))
