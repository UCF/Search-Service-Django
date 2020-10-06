from django.core.management.base import BaseCommand
from programs.models import CIP

import argparse
import csv
import settings

class Command(BaseCommand):
    help = 'Imports CIPs from the default file provided by NCES'

    processed = 0
    created = 0
    updated = 0
    cip_version = ''

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=argparse.FileType('r'),
            help='The CSV file of CIPs to be imported'
        )

        parser.add_argument(
            '--cip-version',
            type=str,
            dest='cip_version',
            help='The CIP version being imported',
            default=settings.CIP_CURRENT_VERSION,
            required=False
        )

    def handle(self, *args, **options):
        f = options['csv_file']
        reader = csv.DictReader(f)
        self.cip_version = options['cip_version']

        self.do_import(reader)
        self.print_stats()

    def do_import(self, reader):
        for row in reader:
            title_def = row['Title & Definition']
            code = row['CIP Code']

            title, definition = title_def.split('.', 1)

            self.create_or_update_cip(title, definition, code)


    def print_stats(self):
        stats = """
All Finished Importing!
-----------------------

Processed: {0}
Created:   {1}
Updated:   {2}
        """.format(
            self.processed,
            self.created,
            self.updated
        )

        print(stats)

    def create_or_update_cip(self, title, definition, cip_code):
        try:
            existing_cip = CIP.objects.get(code=cip_code, version=self.cip_version)

            if existing_cip.name != title or existing_cip.description != definition:
                existing_cip.name = title
                existing_cip.description = definition
                existing_cip.save()
                self.updated += 1
        except CIP.DoesNotExist:
            new_cip = CIP(
                name=title,
                description=definition,
                code=cip_code,
                version=self.cip_version
            )

            new_cip.save()

            self.created += 1

        self.processed += 1
