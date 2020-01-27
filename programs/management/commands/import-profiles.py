from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import json
from tabulate import tabulate

class Command(BaseCommand):
    help = """
Imports URLs for ProgramProfiles from a WordPress blog
    """
    path = None
    profile_type = None
    set_primary = True

    page  = 0
    pages = 0

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

    def handle(self, *args, **options):
        self.path = options['path']
        profile_type = options['profile_type']
        self.set_primary = options['primary']

        try:
            self.profile_type = ProgramProfileType.objects.get(name=profile_type)
        except:
            raise CommandError("\"{0}\" is not a valid ProgramProfileType.".format(profile_type))

        self.import_profiles()
        self.print_stats()

    def import_profiles(self):
        response = urllib2.urlopen(self.path)

        headers = dict(response.info())

        if headers.has_key('x-wp-totalpages'):
            self.pages = int(headers['x-wp-totalpages'])

        programs = json.loads(response.read())
        self.process_page(programs)

        if self.pages > 1:
            for page in xrange(2, self.pages):
                path = "{0}?page={1}".format(self.path, page)
                response = urllib2.urlopen(path)

                programs = json.loads(response.read())

                self.process_page(programs)


    def process_page(self, programs):
        for program in programs:
            plan_code = program['degree_meta']['degree_code']
            subplan_code = program['degree_meta']['degree_subplan_code']

            try:
                prg_obj = Program.objects.get(plan_code=plan_code, subplan_code=subplan_code)
            except:
                continue

            try:
                existing = ProgramProfile.objects.get(program=prg_obj, profile_type=self.profile_type)
                if existing.url != program['link']:
                    existing.url = program['link']
                    existing.primary = self.set_primary
                    existing.save()
                else:
                    continue
            except:
                profile = ProgramProfile(
                    program=prg_obj,
                    profile_type=self.profile_type,
                    primary=self.set_primary,
                    url=program['link']
                )
                profile.save()

    def print_stats(self):
        pass


