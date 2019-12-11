from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import decimal
import urllib2
import itertools
import logging
import sys
import csv
import ssl


class Command(BaseCommand):
    help = 'Imports program outcome statistics from a CSV'

    socs_data = []
    socs_count = 0
    socs_added = 0
    socs_skipped = 0

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=file,
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
        if self.socs_count > 0:
            SOC.objects.all().delete()

        for soc in self.socs_data:
            cip_code = soc['CIP Code'].strip()
            cip_title = soc['CIP Title'].strip()
            soc_code = soc['SOC Code'].strip()
            soc_title = soc['SOC Title'].strip()

            # Get the CIP
            try:
                cip = CIP.objects.get(code=cip_code, version=self.cip_version)
            except Exception, e:
                cip = None

            if cip is not None and soc_code != 'NO MATCH':

                new_soc = SOC(
                    name=cip_title,
                    code=soc_code,
                    version=self.soc_version,
                    cip=cip
                )

                new_soc.save()

                self.socs_added += 1
            else:
                self.socs_skipped +=1

    def print_results(self):
        print 'Finished import of SOC data.'
        if self.socs_added:
            print 'Created and associated {0} SOC codes.'.format(self.socs_added)
        if self.socs_skipped:
            print 'Skipped {0} SOC codes.'.format(self.socs_skipped)
