from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import logging
import sys
import csv
import mimetypes

from argparse import FileType


class Command(BaseCommand):
    help = 'Imports Occupational codes (SOC) and associates them with Instructional Program codes (CIP)'

    socs_data = []
    socs_count = 0
    socs_added = 0
    socs_updated = 0
    socs_skipped = 0

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=FileType('r', encoding='utf-8-sig'),
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

    def handle(self, *args, **options):
        self.file = options['file']
        self.loglevel = options['loglevel']
        self.cip_version = options['cip_version']
        self.soc_version = options['soc_version']

        mime_type, encoding = mimetypes.guess_type(self.file.name)

        if mime_type != 'text/csv':
            raise Exception('File provided does not have a mimetype of "text/csv"')

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Fetch all outcome data:
        self.get_socs(self.file)

        # Assign outcome data to existing programs:
        self.assign_socs()

        # Print results
        self.print_results()

    def get_socs(self, csv_file):

        try:
            csv_reader = csv.DictReader(csv_file)
        except csv.Error:
            logging.error('\n ERROR reading CSV: CSV does not have valid headers or is malformed.')
            return

        for row in csv_reader:
            self.socs_data.append(row)

        self.socs_count = len(self.socs_data)

    def assign_socs(self):
        for soc in self.socs_data:
            cip_code = soc['CIP Code'].strip()
            cip_title = soc['CIP Title'].strip()
            soc_code = soc['SOC Code'].strip()
            soc_title = soc['SOC Title'].strip()

            # Get the CIP
            try:
                cip = CIP.objects.get(code=cip_code, version=self.cip_version)
            except Exception as e:
                cip = None

            if cip is not None and soc_code != 'NO MATCH':
                try:
                    existing = SOC.objects.get(code=soc_code, version=self.soc_version)
                    existing.name = soc_title
                    existing.cip.add(cip)
                    existing.save()

                    self.socs_updated += 1
                except SOC.DoesNotExist:
                    new_soc = SOC(
                        name=soc_title,
                        code=soc_code,
                        version=self.soc_version
                    )

                    new_soc.save()

                    new_soc.cip.add(cip)
                    self.socs_added += 1
            else:
                self.socs_skipped +=1

    def print_results(self):
        created_percent = (float(self.socs_added) / float(self.socs_count)) * 100 if self.socs_added > 0 else 0
        updated_percent = (float(self.socs_updated) / float(self.socs_count)) * 100 if self.socs_updated > 0 else 0
        skipped_percent = (float(self.socs_skipped) / float(self.socs_count)) * 100 if self.socs_skipped > 0 else 0

        print('\nFinished import of SOC (Occupational) data.\n')

        print('Processed: {0}'.format(self.socs_count))
        print('Created:   {0} ({1}%)'.format(self.socs_added, round(created_percent)))
        print('Updated:   {0} ({1}%)'.format(self.socs_updated, round(updated_percent)))
        print('Skipped:   {0} ({1}%)'.format(self.socs_skipped, round(skipped_percent)))
