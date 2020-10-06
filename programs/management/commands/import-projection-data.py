from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import argparse
import decimal
import logging
import sys
import csv
import mimetypes


class Command(BaseCommand):
    help = 'Imports Bureau of Labor Statistics Employment projections'

    projection_data = []
    projections_added = 0
    projections_skipped = 0
    jobs_added = 0
    jobs_assigned = 0

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=argparse.FileType('r'),
            help='The file path of the csv file'
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
        parser.add_argument(
            '--soc-version',
            type=str,
            dest='soc_version',
            help='The version of the SOC specification to set.',
            default=settings.SOC_CURRENT_VERSION,
            required=False
        )
        parser.add_argument(
            '--report-version',
            type=str,
            dest='report_version',
            help='The version of the report being imported. Usually a range of years.',
            default=settings.PROJ_CURRENT_REPORT,
            required=False
        )

    def handle(self, *args, **options):
        self.file = options['file']
        self.loglevel = options['loglevel']
        self.cip_version = options['cip_version']
        self.soc_version = options['soc_version']
        self.report_version = options['report_version']

        mime_type, encoding = mimetypes.guess_type(self.file.name)

        if mime_type != 'text/csv':
            raise Exception('File provided does not have a mimetype of "text/csv"')

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Reads all the projection data:
        self.get_projections(self.file)

        # Assigns the projection data to records
        self.assign_projections()

        # Print results
        self.print_results()

    def get_projections(self, csv_file):

        try:
            csv_reader = csv.DictReader(csv_file)
        except csv.Error:
            logging.error('\n ERROR reading CSV: CSV does not have valid headers or is malformed.')
            return

        for row in csv_reader:
            self.projection_data.append(row)

        self.projection_count = len(self.projection_data)

    def assign_projections(self):
        # Clear all employment projections
        EmploymentProjection.objects.filter(report=self.report_version).delete()

        for proj in self.projection_data:
            title_jobs = proj['title']
            title, jobs = self.parse_title(title_jobs)
            code = proj['code']
            begin_value = proj['begin']
            end_value = proj['end']
            change = proj['change']
            change_perc = proj['change_perc']
            openings = proj['openings']

            try:
                soc = SOC.objects.get(code=code, version=self.soc_version)
            except:
                soc = None

            if soc is not None:
                # Only create if the object doesn't already exist
                try:
                    ep = EmploymentProjection.objects.get(soc=soc, report=self.report_version)
                except EmploymentProjection.DoesNotExist:
                    obj = EmploymentProjection(
                        soc=soc,
                        report=self.report_version,
                        begin_employment=self.decimal_to_thousands(begin_value),
                        end_employment=self.decimal_to_thousands(end_value),
                        change=self.decimal_to_thousands(change),
                        change_percentage=decimal.Decimal(change_perc),
                        openings=self.decimal_to_thousands(openings)
                    )

                    obj.save()

                # Add the job positions
                # Clear all postings first
                soc.jobs.clear()

                for job in jobs:
                    if job is None:
                        continue

                    try:
                        position = JobPosition.objects.get(name=job)
                    except JobPosition.DoesNotExist:
                        position = JobPosition(
                            name=job
                        )

                        position.save()
                        self.jobs_added += 1

                    soc.jobs.add(position)
                    self.jobs_assigned += 1

                self.projections_added += 1
            else:
                self.projections_skipped += 1

    def parse_title(self, value):
        parts = value.split('*')
        title = parts.pop(0)
        jobs = list(map(str.strip, parts))

        return (title, jobs)


    def decimal_to_thousands(self, dec):
        if dec:
            # First a string transform
            dec = dec.replace(',', '')
            # Case to float and multiply by a thousand
            amount = float(dec) * 1000
            return round(amount)

        return None

    def print_results(self):
        retval = """
Finished importing projection data.
-----------------------------------

Projection records processed: {0}
Projection records added:     {1}
Projection records skipped:   {2}

-----------------------------------

Job Positions Created:        {3}
Job Positions Assigned:       {4}
        """.format(
            self.projection_count,
            self.projections_added,
            self.projections_skipped,
            self.jobs_added,
            self.jobs_assigned
        )

        print(retval)

