from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import decimal
import urllib2
import itertools
import logging
import sys
import csv


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
        except Exception, e: # TODO
            print e
            # pass # TODO couldn't access file

        try:
            csv_reader = csv.DictReader(response)
        except Exception, e: # TODO
            print e
            #pass # TODO couldn't read file

        for row in csv_reader:
            self.outcome_data.append(row)

    def assign_program_outcomes(self):
        # Only process programs that are not subplans:
        programs = Program.objects.filter(parent_program__isnull=True)
        programs_count = len(programs)
        programs_matched_count = 0
        outcomes_count = len(self.outcome_data)
        outcomes_matched_count = 0
        outcomes_skipped_count = 0

        # If we have new outcome data to process, delete any existing data.
        # Otherwise, abort this process:
        if outcomes_count:
            print 'Deleting all existing outcome data.'
            ProgramOutcomeStat.objects.all().delete()
        else:
            print 'No outcome data to process. Assignment of new program outcome data aborted.'
            return

        for row in self.outcome_data:
            # CIP and year code are required.
            # Skip row if they're missing/invalid
            cip = row['CIP']
            year_code = self.get_outcome_year_code(row['Year'])
            if not cip or not year_code:
                outcomes_skipped_count += 1
                continue

            # Get or create an AcademicYear object
            try:
                year = AcademicYear.objects.get(code=year_code)
            except AcademicYear.DoesNotExist:
                year = AcademicYear(
                    code = year_code,
                    display = row['Year']
                )
                year.save()
            level = self.get_outcome_level(row['Level'])
            employed_full_time = self.percent_to_decimal(row['Employed Full-time %'])
            continuing_education = self.percent_to_decimal(row['Continuing Education'])
            avg_annual_earnings = self.dollars_to_decimal(row['Avg Annual Earnings'])

            outcome_programs = self.get_outcome_programs(programs, cip, level)
            if len(outcome_programs):
                outcome = ProgramOutcomeStat(
                    academic_year = year
                    #employed_full_time = employed_full_time,
                    #continuing_education = continuing_education,
                    #avg_annual_earnings = avg_annual_earnings
                )
                outcome.save()
                outcome.program.add(*outcome_programs)
                outcome.save()



        #    if: # TODO
        #        logging.info(unicode('MATCH \n Matched program name: %s \n Cleaned program name: %s \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n Match score: %d \n' % (p.program.name, p.name_clean, matched_entry.name, matched_entry.name_clean, match.match_score)).encode('ascii', 'xmlcharrefreplace'))
        #    else:
        #        logging.info(unicode('FAILURE \n Matched program name: %s \n Cleaned program name: %s \n' % (p.program.name, p.name_clean)).encode('ascii', 'xmlcharrefreplace'))

        #print 'Matched {0}/{1} of Existing {2} Programs to a Catalog Entry: {3:.0f}%'.format(match_count, len(programs), career_name, float(match_count) / float(len(programs)) * 100)
        #print 'Matched {0}/{1} of Fetched Catalog Entries to at Least One Existing Program: {2:.0f}%'.format(len(filter(lambda x: x.has_matches == True, self.catalog_programs)), len(self.catalog_programs), len(filter(lambda x: x.has_matches == True, self.catalog_programs)) / float(len(self.catalog_programs)) * 100)


    '''
    Returns a Level object based on a outcome row's level value.
    '''
    def get_outcome_level(self, original_level):
        # Remove apostrophes from CSV data levels (e.g. "Bachelor's -> Bachelors")
        temp_level = original_level.replace('\'', '')

        try:
            temp_level = Level.objects.get(name=temp_level)
            return temp_level
        except Level.DoesNotExist:
            temp_level = None

        if self.type == 'Doctorate':
            return Level.objects.get(name='Doctoral')
        elif self.type == 'Medicine':
            return Level.objects.get(name='Professional')

        return None

    '''
    Given a year range string, returns a 4-digit year code suitable
    for an AcademicYear's `code` field.
    '''
    def get_outcome_year_code(self, year_display):
        years = year_display.split('-')
        if len(years) == 2:
            # Return last 2 digits from both parts of the split year range:
            year_start = years[0][-2:]
            year_end = years[1][-2:]
            return year_start + year_end

        return None

    '''
    Return Program(s) that match against a given CIP and program level.
    '''
    def get_outcome_programs(self, programs, cip, level):
        return list(programs.filter(cip_code=cip, level=level))

    '''
    Converts a string with a percentage value to a Decimal.
    Returns None if the given string is false-y.
    '''
    def percent_to_decimal(self, percent):
        decimal.getcontext().prec = 8
        if percent:
            return decimal.Decimal(percent.replace('%', '').strip())

        return None

    '''
    Converts a dollar amount string to a Decimal.
    Returns None if the given string is false-y.
    '''
    def dollars_to_decimal(self, dollars):
        decimal.getcontext().prec = 2
        if dollars:
            return decimal.Decimal(dollars.replace('$', '').replace(',', '').strip())

        return None
