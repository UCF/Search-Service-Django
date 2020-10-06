from django.core.management.base import BaseCommand
from images.models import *

import argparse
import csv
import datetime
import json
import logging
import mimetypes
import timeit

from progress.bar import Bar
from unidecode import unidecode


class Command(BaseCommand):
    help = 'Imports all existing image tags from UCF\'s Tandem Vault instance.'

    progress_bar = Bar('Processing')
    source = 'Tandem Vault'
    tags = []
    tag_count = 0
    tags_created = 0
    tags_updated = 0
    tags_skipped = 0
    synonyms_assigned = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=argparse.FileType('r'),
            help='''\
            CSV file containing existing tag and synonym information
            from Tandem Vault
            ''',
            dest='file',
            required=True
        )

    def handle(self, *args, **options):
        self.tandemvault_tags_csv = options['file']

        # Start a timer for the bulk of the script
        self.exec_time = 0
        self.exec_start = timeit.default_timer()

        # Process the CSV
        self.load_tandemvault_tags()
        self.process_tandemvault_tags()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(
            seconds=self.exec_end - self.exec_start
        )

        # Print the results
        self.progress_bar.finish()
        self.print_stats()

        return

    '''
    Load a CSV of Tandem Vault tags + synonyms.
    '''
    def load_tandemvault_tags(self):
        # The csv lib will happily process pretty much any file
        # you throw at it; do some really rudimentary checking
        # against the file name before continuing:
        try:
            mime = mimetypes.guess_type(self.tandemvault_tags_csv.name)[0]
        except Exception as e:
            logging.error(
                '\nError reading CSV: couldn\'t verify mimetype of file'
            )
            return

        if mime != 'text/csv':
            logging.error(
                (
                    '\nError reading CSV: expected file with mimetype '
                    '"text/csv"; got "{0}"'
                )
                .format(mime)
            )
            return

        try:
            csv_reader = csv.DictReader(self.tandemvault_tags_csv)
        except csv.Error as e:
            logging.error(
                '\nError reading CSV: {0}'
                .format(e)
            )
            return

        for row in csv_reader:
            self.tags.append(row)

        self.tag_count = len(self.tags)

    '''
    Process loaded Tandem Vault tags.
    '''
    def process_tandemvault_tags(self):
        for tandemvault_tag in self.tags:
            name = self.clean_tag_name(tandemvault_tag['name'])
            # Empty tags can exist in this data for whatever reason;
            # skip them if present
            if not name:
                self.tags_skipped += 1
                continue

            synonyms = [_f for _f in [self.clean_tag_name(synonym) for synonym in json.loads(tandemvault_tag['synonym_names'])] if _f]

            try:
                tag = ImageTag.objects.get(name=name)
                self.tags_updated += 1
            except ImageTag.DoesNotExist:
                tag = ImageTag(
                    name=name,
                    source=self.source
                )
                tag.save()
                self.tags_created += 1

            # Remove existing Tandem Vault synonym relationships
            existing_synonyms = tag.synonyms.filter(source=self.source)
            if existing_synonyms:
                tag.synonyms.remove(*existing_synonyms)

            # Assign fresh Tandem Vault synonym relationships
            for synonym in synonyms:
                try:
                    s = ImageTag.objects.get(name=synonym)
                except ImageTag.DoesNotExist:
                    s = ImageTag(
                        name=synonym,
                        source=self.source
                    )
                    s.save()
                tag.synonyms.add(s)
                self.synonyms_assigned += 1

            tag.save()

    '''
    Sanitizes tag names
    '''
    def clean_tag_name(self, name):
        try:
            name = name.encode('utf-8').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # we tried; make it behave
            name = unidecode(name)

        return name.lower().strip()

    '''
    Displays information about the import.
    '''
    def print_stats(self):
        stats = '''\
Finished import of {0} Tandem Vault image tags.

Created: {1}
Updated: {2}
Skipped: {3}
Synonyms assigned: {4}

Script executed in {5}
        '''.format(
            self.tag_count,
            self.tags_created,
            self.tags_updated,
            self.tags_skipped,
            self.synonyms_assigned,
            self.exec_time
        )

        print(stats)
