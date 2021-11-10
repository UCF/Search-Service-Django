from django.core.management.base import BaseCommand, CommandError

from units.models import College
from units.models import Department
from units.models import Division
from units.models import Organization
from units.utils import Utilities

class Command(BaseCommand):
    help = 'Sanitizes external organization, division, college and department names'

    def handle(self, *args, **options):
        self.colleges_processed = College.objects.all()
        self.orgs_processed = Organization.objects.all()
        self.divisions_processed = Division.objects.all()
        self.departments_processed = Department.objects.all()

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

    def print_stats(self):
        msg = f"""
Colleges Updated      : {self.colleges_processed.count()}
Organizations Updated : {self.orgs_processed.count()}
Divisions Updated     : {self.divisions_processed.count()}
Departments Updated   : {self.departments_processed.count()}
        """

        self.stdout.write(self.style.SUCCESS(msg))
