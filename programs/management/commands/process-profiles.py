from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import settings
from tabulate import tabulate

class Command(BaseCommand):
    help = """
Processes program profiles and sets the primary profile
based on the values set in PROGRAM_PROFILE constant in
the settings_local.py file.
    """
    programs_processed = 0
    programs_updated = 0
    programs_unable = 0
    programs_no_change = 0
    programs_missing = 0

    def handle(self, *args, **options):
        """
        Handles the process-profiles command.
        """
        self.update_programs()
        self.print_stats()

    def update_programs(self):
        """
        Handles updating the programs
        """
        programs = Program.objects.all()

        for program in programs:
            self.programs_processed += 1

            profile_type = program.primary_profile_type

            if profile_type == None:
                self.programs_unable += 1
                continue

            profile = program.profiles.filter(profile_type=profile_type).first()

            if profile is not None:
                if profile.primary == False:
                    profile.primary = True
                    profile.save()
                    program.profiles.exclude(pk=profile.pk).update(primary=False)
                    self.programs_updated += 1
                else:
                    self.programs_no_change += 1
            else:
                self.programs_missing += 1

    def print_stats(self):
        results = [
            ("Programs Processed", self.programs_processed),
            ("Programs Updated", self.programs_updated),
            ("Programs With No Changes", self.programs_no_change),
            ("Programs Unable to be Updated", self.programs_unable),
            ("Programs With Missing Profile", self.programs_missing)
        ]

        self.stdout.write('''
Complete!

        ''')

        self.stdout.write(tabulate(results, tablefmt='grid'), ending='\n\n')
