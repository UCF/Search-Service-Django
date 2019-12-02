from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import itertools
import logging
import sys
import csv


# class OutcomeEntry(object):

#     def __init__(self, data_row):
#         self.year = ''
#         self.cip = ''
#         self.original_level = ''
#         self.employed_full_time = ''
#         self.continuing_education = ''
#         self.avg_annual_earnings = ''

#     # Returns a sanitized Level value
#     @property
#     def level(self):
#         # Remove apostrophes from CSV data levels (e.g. "Bachelor's -> Bachelors")
#         temp_level = original_level.replace('\'', '')

#         try:
#             temp_level = Level.objects.get(name=self.original_level)
#             return temp_level
#         except Level.DoesNotExist:
#             temp_level = None

#         if self.type == 'Doctorate':
#             return Level.objects.get(name='Doctoral')
#         elif self.type == 'Medicine':
#             return Level.objects.get(name='Professional')

#         return None


class Command(BaseCommand):
    help = 'Imports program outcome statistics from a CSV'

    outcome_data = []

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='The base url of the outcomes data CSV'
        )
        parser.add_argument(
            '--verbose',
            help='Be verbose',
            action='store_const',
            dest='loglevel',
            const=logging.INFO,
            default=logging.WARNING,
            required=False
        )

    def handle(self, *args, **options):
        self.path = options['path']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Fetch all outcome data; assign to self.outcome_data:
        self.get_outcome_data(self.path)

        # Assign outcome data to existing programs:
        self.assign_program_outcomes()

        return 0

    def get_outcome_data(self, csv_url):
        try:
            response = urllib2.urlopen(csv_url)
            #raw_data = response.read()
        except Exception, e: # TODO
            pass # TODO couldn't access file

        try:
            csv_reader = csv.DictReader(response)
        except Exception, e: # TODO
            pass # TODO couldn't read file

        for row in csv_reader:
            #self.outcome_data.append(OutcomeEntry(row))
            self.outcome_data.append(row)

    def assign_program_outcomes(self):
        # Only process programs that are not subplans:
        programs = Program.objects.filter(parent_program__isnull=True)
        program_count = programs.count()
        programs_matched_count = 0
        outcomes_count = self.outcome_data.count()
        outcomes_matched_count = 0

        for p in programs:
            # Wipe out any existing outcome data
            p.outcomes = None
            p.save()

        #    if: # TODO
        #        logging.info(unicode('MATCH \n Matched program name: %s \n Cleaned program name: %s \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n Match score: %d \n' % (p.program.name, p.name_clean, matched_entry.name, matched_entry.name_clean, match.match_score)).encode('ascii', 'xmlcharrefreplace'))
        #    else:
        #        logging.info(unicode('FAILURE \n Matched program name: %s \n Cleaned program name: %s \n' % (p.program.name, p.name_clean)).encode('ascii', 'xmlcharrefreplace'))

        #print 'Matched {0}/{1} of Existing {2} Programs to a Catalog Entry: {3:.0f}%'.format(match_count, len(programs), career_name, float(match_count) / float(len(programs)) * 100)
        #print 'Matched {0}/{1} of Fetched Catalog Entries to at Least One Existing Program: {2:.0f}%'.format(len(filter(lambda x: x.has_matches == True, self.catalog_programs)), len(self.catalog_programs), len(filter(lambda x: x.has_matches == True, self.catalog_programs)) / float(len(self.catalog_programs)) * 100)


    def get_level(self, original_level):
        # Remove apostrophes from CSV data levels (e.g. "Bachelor's -> Bachelors")
        temp_level = original_level.replace('\'', '')

        try:
            temp_level = Level.objects.get(name=self.original_level)
            return temp_level
        except Level.DoesNotExist:
            temp_level = None

        if self.type == 'Doctorate':
            return Level.objects.get(name='Doctoral')
        elif self.type == 'Medicine':
            return Level.objects.get(name='Professional')

        return None
