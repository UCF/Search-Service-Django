from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import ssl
import json
from progress.bar import ChargingBar
from tabulate import tabulate

class Command(BaseCommand):
    help = """
Imports URLs for ProgramProfiles from a WordPress blog
    """
    path = None
    profile_type = None
    set_primary = True
    plan_code_field = 'degree_code'
    subplan_code_field = 'degree_subplan_code'
    remove_stale = False

    page  = 0
    pages = 0

    found_profiles = []

    degrees_found = 0
    degrees_processed = 0
    degrees_matched = 0
    degrees_skipped = 0

    profiles_created = 0
    profiles_updated = 0
    profiles_skipped = 0
    profiles_removed = 0

    progress_bar = None

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='The URL of the WordPress blog to import profiles from.'
        )

        parser.add_argument(
            'profile_type',
            type=str,
            help='The profile type to assign the profiles to.'
        )

        parser.add_argument(
            '--primary',
            type=bool,
            dest='primary',
            default=True
        )

        parser.add_argument(
            '--plan-code-field',
            type=str,
            dest='plan_code_field',
            default='degree_code'
        )

        parser.add_argument(
            '--subplan-code-field',
            type=str,
            dest='subplan_code_field',
            default='degree_subplan_code'
        )

        parser.add_argument(
            '--remove-stale',
            type=bool,
            dest='remove_stale',
            default=False
        )

    def handle(self, *args, **options):
        self.path = options['path']
        profile_type = options['profile_type']
        self.set_primary = options['primary']
        self.plan_code_field = options['plan_code_field']
        self.subplan_code_field = options['subplan_code_field']
        self.remove_stale = options['remove_stale']

        try:
            self.profile_type = ProgramProfileType.objects.get(name=profile_type)
        except:
            raise CommandError("\"{0}\" is not a valid ProgramProfileType.".format(profile_type))

        self.import_profiles()

        if self.progress_bar:
            self.progress_bar.finish()

        if self.remove_stale:
            self.remove_stale_profiles()

        self.print_stats()

    def import_profiles(self):
        context = ssl._create_unverified_context()

        response = urllib2.urlopen(self.path, context=context)

        headers = dict(response.info())

        if headers.has_key('x-wp-totalpages'):
            self.pages = int(headers['x-wp-totalpages'])

        if headers.has_key('x-wp-total'):
            self.degrees_found = int(headers['x-wp-total'])
            self.progress_bar = ChargingBar('Processing', max=self.degrees_found)

        programs = json.loads(response.read())
        self.process_page(programs)

        if self.pages > 1:
            for page in range(2, self.pages + 1):
                path = "{0}?page={1}".format(self.path, page)
                response = urllib2.urlopen(path, context=context)

                programs = json.loads(response.read())

                self.process_page(programs)


    def process_page(self, programs):
        for program in programs:
            self.degrees_processed += 1
            self.progress_bar.next()
            plan_code = program['degree_meta'][self.plan_code_field] if self.plan_code_field in program['degree_meta'] else None
            subplan_code = program['degree_meta'][self.subplan_code_field] if self.subplan_code_field in program['degree_meta'] else None

            try:
                if plan_code:
                    prg_obj = Program.objects.get(plan_code=plan_code, subplan_code=subplan_code)
                    self.degrees_matched += 1
                else:
                    self.degrees_skipped += 1
            except:
                self.degrees_skipped += 1
                continue

            try:
                existing = ProgramProfile.objects.get(program=prg_obj, profile_type=self.profile_type)
                self.found_profiles.append(existing.id)
                if existing.url != program['link']:
                    existing.url = program['link']
                    existing.primary = self.set_primary
                    existing.save()
                    self.profiles_updated += 1
                else:
                    self.profiles_skipped += 1
                    continue
            except:
                profile = ProgramProfile(
                    program=prg_obj,
                    profile_type=self.profile_type,
                    primary=self.set_primary,
                    url=program['link']
                )
                profile.save()
                self.found_profiles.append(profile.id)
                self.profiles_created += 1

    def remove_stale_profiles(self):
        not_processed = ProgramProfile.objects.filter(profile_type=self.profile_type).exclude(id__in=self.found_profiles)
        self.profiles_removed = len(not_processed)
        if self.profiles_removed > 0:
            not_processed.delete()

    def print_stats(self):
        results = [
            ("Degrees Found", self.degrees_found),
            ("Degrees Processed", self.degrees_processed),
            ("Degress Matched", self.degrees_matched),
            ("Degrees Skipped", self.degrees_skipped),
            ("Profiles Created", self.profiles_created),
            ("Profiles Updated", self.profiles_updated),
            ("Profiles Skipped (No Update Needed)", self.profiles_skipped),
            ("Profiles Removed (Stale)", self.profiles_removed)
        ]

        self.stdout.write('''
Complete!
        ''')

        self.stdout.write(tabulate(results, tablefmt='grid'), ending='\n\n')

