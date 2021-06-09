from django.core.management.base import BaseCommand, CommandError
from org_units.models import *
from teledata.models import Organization as TeledataOrg
from programs.models import College
from teledata.models import Department as TeledataDept
from programs.models import Department as ProgramDept

from progress.bar import ChargingBar


class Command(BaseCommand):
    help = 'Assigns relationships across various apps for organizations and departments'

    teledata_orgs_processed = 0
    colleges_processed = 0
    org_units_created = 0
    org_units_updated = 0
    org_units_deleted = 0
    teledata_depts_processed = 0
    program_depts_processed = 0
    dept_units_created = 0
    dept_units_updated = 0
    dept_units_deleted = 0

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.
        """
        self.map_orgs()
        self.map_depts()
        self.delete_stale_orgs()
        self.delete_stale_depts()
        self.print_stats()

    def map_orgs(self):
        """
        Performs mapping for all Organization-related data
        """
        self.map_orgs_teledata()
        self.map_orgs_colleges()

    def map_orgs_teledata(self):
        """
        TODO
        """
        teledata_orgs = TeledataOrg.objects.all()
        self.teledata_orgs_processed = len(teledata_orgs)

        if len(teledata_orgs):
            return
        return

    def map_orgs_colleges(self):
        """
        TODO
        """
        return

    def map_depts(self):
        """
        Performs mapping for all Department-related data
        """
        self.map_depts_teledata()
        self.map_depts_programs()

    def map_depts_teledata(self):
        """
        TODO
        """
        return

    def map_depts_programs(self):
        """
        TODO
        """
        return

    def delete_stale_orgs(self):
        """
        TODO
        """
        return

    def delete_stale_depts(self):
        """
        TODO
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
            self.teledata_orgs_processed,
            self.colleges_processed,
            self.org_units_created,
            self.org_units_updated,
            self.org_units_deleted,
            self.teledata_depts_processed,
            self.program_depts_processed,
            self.dept_units_created,
            self.dept_units_updated,
            self.dept_units_deleted
        )

        self.stdout.write(stats)
