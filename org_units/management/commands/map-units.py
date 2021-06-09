from django.core.management.base import BaseCommand, CommandError
from org_units.models import *
from teledata.models import Organization as TeledataOrg
from programs.models import College
from teledata.models import Department as TeledataDept
from programs.models import Department as ProgramDept

from progress.bar import ChargingBar


class Command(BaseCommand):
    help = 'Assigns relationships across various apps for organizations and departments'

    teledata_orgs_processed = set()
    colleges_processed = set()
    org_units_created = set()
    org_units_updated = set()
    org_units_deleted_count = 0
    teledata_depts_processed = set()
    program_depts_processed = set()
    dept_units_created = set()
    dept_units_updated = set()
    dept_units_deleted_count = 0

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.
        """
        self.map_orgs()
        self.map_depts()
        self.delete_stale_orgs()
        self.delete_stale_depts()
        self.assign_depts_to_orgs()
        self.print_stats()

    def sanitize_unit_name(self, unit_name):
        """
        Sanitizes and normalizes the name of an organization
        or department for consistency and to make cross-app
        string matching possible
        """
        return unit_name

    def get_org_by_name(self, name):
        """
        Retrieves an Organization by its sanitized name.
        Handles incrementing of script created/updated flags.
        """
        org_name_sanitized = self.sanitize_unit_name(name)
        if org_name_sanitized:
            org_unit, created = Organization.objects.get_or_create(
                name=org_name_sanitized
            )
            if created:
                self.org_units_created.add(org_unit)
            elif org_unit not in self.org_units_created:
                self.org_units_updated.add(org_unit)

            return org_unit
        else:
            return None

    def get_dept_by_name(self, name):
        """
        Retrieves a Department by its sanitized name.
        Handles incrementing of script created/updated flags.
        """
        dept_name_sanitized = self.sanitize_unit_name(name)
        if dept_name_sanitized:
            dept_unit, created = Department.objects.get_or_create(
                name=dept_name_sanitized
            )
            if created:
                self.dept_units_created.add(dept_unit)
            elif dept_unit not in self.dept_units_created:
                self.dept_units_updated.add(dept_unit)

            return dept_unit
        else:
            return None

    def map_orgs(self):
        """
        Performs mapping for all Organization-related data
        """
        self.map_orgs_teledata()
        self.map_orgs_colleges()

    def map_orgs_teledata(self):
        """
        Gets or creates an Organization from corresponding
        teledata, and maps the teledata to the Organization.
        """
        teledata_orgs = TeledataOrg.objects.all()
        self.teledata_orgs_processed = teledata_orgs

        for teledata_org in teledata_orgs:
            org_unit = self.get_org_by_name(teledata_org.name)
            if org_unit:
                org_unit.teledata = teledata_org
                org_unit.save()
            # If there was an `organization_unit` reverse relationship
            # previously assigned to the teledata object and we can no
            # longer make an association, delete the old relationship:
            elif teledata_org.organization_unit is not None:
                teledata_org.organization_unit = None
                teledata_org.save()

    def map_orgs_colleges(self):
        """
        Gets or creates an Organization from corresponding
        College data, and maps the College to the Organization.
        """
        colleges = College.objects.all()
        self.colleges_processed = colleges

        for college in colleges:
            org_unit = self.get_org_by_name(college.full_name)
            if org_unit:
                org_unit.college = college
                org_unit.save()
            # If there was an `organization_unit` reverse relationship
            # previously assigned to the College and we can no longer
            # make an association, delete the old relationship:
            elif college.organization_unit is not None:
                college.organization_unit = None
                college.save()

    def map_depts(self):
        """
        Performs mapping for all Department-related data
        """
        self.map_depts_teledata()
        self.map_depts_programs()

    def map_depts_teledata(self):
        """
        Gets or creates a Department from corresponding
        teledata, and maps the teledata to the Department.
        """
        teledata_depts = TeledataDept.objects.all()
        self.teledata_depts_processed = teledata_depts

        for teledata_dept in teledata_depts:
            dept_unit = self.get_dept_by_name(teledata_dept.name)
            if dept_unit:
                dept_unit.teledata = teledata_dept
                dept_unit.save()
            # If there was a `department_unit` reverse relationship
            # previously assigned to the teledata object and we can no longer
            # make an association, delete the old relationship:
            elif teledata_dept.department_unit is not None:
                teledata_dept.department_unit = None
                teledata_dept.save()

    def map_depts_programs(self):
        """
        Gets or creates a Department from corresponding
        program data, and maps the program data to the Department.
        """
        program_depts = ProgramDept.objects.all()
        self.program_depts_processed = program_depts

        for program_dept in program_depts:
            dept_unit = self.get_dept_by_name(program_dept.full_name)
            if dept_unit:
                dept_unit.program_data = program_dept
                dept_unit.save()
            # If there was a `department_unit` reverse relationship
            # previously assigned to the `program_dept` and we can no longer
            # make an association, delete the old relationship:
            elif program_dept.department_unit is not None:
                program_dept.department_unit = None
                program_dept.save()

    def delete_stale_orgs(self):
        """
        Deletes Organizations that no longer have any
        external ForeignKey relationships.
        """
        stale_orgs = Organization.objects.filter(
            teledata__isnull=True,
            college__isnull=True
        )
        self.org_units_deleted = len(stale_orgs)

        if len(stale_orgs):
            stale_orgs.delete()

    def delete_stale_depts(self):
        """
        Deletes Departments that no longer have any
        external ForeignKey relationships.
        """
        stale_depts = Department.objects.filter(
            teledata__isnull=True,
            program_data__isnull=True
        )
        self.dept_units_deleted = len(stale_depts)

        if len(stale_depts):
            stale_depts.delete()

    def assign_depts_to_orgs(self):
        """
        TODO
        Assigns ForeignKey relationships from Departments to
        Organizations, based on inferred teledata and program data.
        """
        return

    def print_stats(self):
        stats = """
Organizations from Teledata processed : {0}
Colleges from Programs processed      : {1}
Organization Units created            : {2}
Organization Units updated            : {3}
Organization Units deleted            : {4}
Departments from Teledata processed   : {5}
Departments from Programs processed   : {6}
Department Units created              : {7}
Department Units updated              : {8}
Department Units deleted              : {9}
        """.format(
            len(self.teledata_orgs_processed),
            len(self.colleges_processed),
            len(self.org_units_created),
            len(self.org_units_updated),
            self.org_units_deleted_count,
            len(self.teledata_depts_processed),
            len(self.program_depts_processed),
            len(self.dept_units_created),
            len(self.dept_units_updated),
            self.dept_units_deleted_count
        )

        self.stdout.write(stats)
