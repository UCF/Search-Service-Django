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

    programs = []
    programs_count = 0
    programs_matched = set()
    outcome_data = []
    outcomes_count = 0
    outcomes_matched_count = 0
    outcomes_skipped_count = 0

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='The base url of the outcomes data CSV'
        )
        parser.add_argument(
            '--verbose',
            help='Use verbose logging',
            action='store_const',
            dest='loglevel',
            const=logging.INFO,
            default=logging.WARNING,
            required=False
        )
        parser.add_argument(
            '--cip-version',
            type=str,
            dest='cip_version',
            help='The version of CIPs used by programs in this import.',
            default=settings.CIP_CURRENT_VERSION,
            required=False
        )

    def handle(self, *args, **options):
        self.path = options['path']
        self.loglevel = options['loglevel']
        self.cip_version = options['cip_version']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Fetch programs (only process programs that have a CIP):
        self.programs = Program.objects.filter(cip__version=self.cip_version)
        self.programs_count = len(self.programs)

        # Fetch all outcome data:
        self.get_outcome_data(self.path)

        # Assign outcome data to existing programs:
        self.assign_program_outcomes()

        # Print results
        self.print_results()

    def get_outcome_data(self, csv_url):
        try:
            context = ssl.SSLContext()
            response = urllib2.urlopen(csv_url, context=context)
            http_message = response.info()
            if http_message.type != 'text/csv':
                raise Exception('File retrieved does not have a mimetype of "text/csv"')
        except Exception, e:
            logging.error('\n ERROR opening CSV: %s' % e)
            return

        try:
            csv_reader = csv.DictReader(response)
        except csv.Error:
            logging.error('\n ERROR reading CSV: CSV does not have valid headers or is malformed.')
            return

        for row in csv_reader:
            self.outcome_data.append(row)

        self.outcomes_count = len(self.outcome_data)

    def assign_program_outcomes(self):
        # If we have new outcome data to process, delete any existing data.
        # Otherwise, abort this process:
        if self.outcomes_count:
            print 'Deleting all existing outcome data.'
            ProgramOutcomeStat.objects.all().delete()
        else:
            print 'No outcome data to process. Assignment of new program outcome data aborted.'
            return

        for row in self.outcome_data:
            # CIP and year code are required.
            # Skip row if they're missing/invalid
            cip = self.get_outcome_cip(row['CIP'])
            year_code = self.get_outcome_year_code(row['Year'])
            if not cip or not year_code:
                self.outcomes_skipped_count += 1
                logging.info(unicode('\n SKIPPED Outcome Data with Year "%s", CIP "%s", and Level "%s"' % (row['Year'], row['CIP'], row['Level'])).encode('ascii', 'xmlcharrefreplace'))
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
            continuing_education = self.percent_to_decimal(row['Continuing Education %'])
            avg_annual_earnings = self.dollars_to_decimal(row['Avg Annual Earnings'])

            outcome_programs = self.get_outcome_programs(cip, level)
            if len(outcome_programs):
                outcome, created = ProgramOutcomeStat.objects.get_or_create(
                    academic_year = year,
                    cip = cip
                )
                outcome.employed_full_time = employed_full_time
                outcome.continuing_education = continuing_education
                outcome.avg_annual_earnings = avg_annual_earnings
                outcome.save()

                for program in outcome_programs:
                    program.outcomes.add(outcome)
                    program.save()

                # Update import stats
                self.programs_matched.update(outcome_programs)
                self.outcomes_matched_count += 1
                logging.info(unicode('\n MATCH Outcome Data with Year "%s", CIP "%s", and Level "%s" to %d existing programs' % (year.display, cip.code, level.name, len(outcome_programs))).encode('ascii', 'xmlcharrefreplace'))
            else:
                self.outcomes_skipped_count += 1
                logging.info(unicode('\n FAILURE Outcome Data with Year "%s", CIP "%s", and Level "%s" - no program matches found' % (year.display, cip.code, level.name)).encode('ascii', 'xmlcharrefreplace'))


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

        if original_level == 'Doctorate':
            return Level.objects.get(name='Doctoral')
        elif original_level == 'Medicine':
            return Level.objects.get(name='Professional')

        return None

    '''
    Given a CIP code string, returns a CIP object under the
    current CIP version.
    '''
    def get_outcome_cip(self, cip_code):
        cip = None
        try:
            cip = CIP.objects.get(code=cip_code, version=self.cip_version)
        except CIP.DoesNotExist:
            pass

        return cip

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
    def get_outcome_programs(self, cip, level):
        return list(self.programs.filter(level=level, cip__in=[cip]))

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

    def print_results(self):
        print 'Finished import of Program Outcome data.'
        if self.programs_count:
            print 'Created one or more ProgramOutcomeStats for {0}/{1} existing Programs with a CIP: {2:.0f}%'.format(len(self.programs_matched), self.programs_count, float(len(self.programs_matched)) / float(self.programs_count) * 100)
        if self.outcomes_count:
            print 'Matched {0}/{1} of fetched Outcome data rows to at least one existing Program: {2:.0f}%'.format(self.outcomes_matched_count, self.outcomes_count, float(self.outcomes_matched_count) / float(self.outcomes_count) * 100)
            print 'Skipped {0} rows of Outcome data.'.format(self.outcomes_skipped_count)
