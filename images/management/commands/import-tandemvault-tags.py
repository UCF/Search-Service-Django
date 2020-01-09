from django.core.management.base import BaseCommand
from images.models import *

import csv
import datetime
import json
import logging
import timeit

from progress.bar import Bar
from unidecode import unidecode


class Command(BaseCommand):
    help = 'Imports all existing image tags from UCF\'s Tandem Vault instance.'

    progress_bar = Bar('Processing')
    source       = 'Tandem Vault'
    tags         = []
    tag_count    = 0
    tags_created = 0
    tags_updated = 0
    tags_deleted = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=file,
            help='CSV file containing existing tag and synonym information from Tandem Vault',
            dest='file',
            required=True
        ),
        parser.add_argument(
            '--delete-stale',
            type=bool,
            help='Whether or not stale tags (tags not assigned to any Images) should be deleted.',
            dest='delete-stale',
            default=False,
            required=False
        )

    def handle(self, *args, **options):
        self.tandemvault_tags_csv = options['file']
        self.do_delete_stale = options['delete-stale']

        # Start a timer for the bulk of the script
        self.exec_time = 0
        self.exec_start = timeit.default_timer()

        # Process the CSV
        self.load_tandemvault_tags()
        self.process_tandemvault_tags()

        # Delete stale Tandem Vault image tags
        if self.do_delete_stale:
            self.delete_stale()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(seconds=self.exec_end - self.exec_start)

        # Print the results
        self.progress_bar.finish()
        self.print_stats()

        return

    '''
    Load a CSV of Tandem Vault tags + synonyms.
    '''
    def load_tandemvault_tags(self):
        try:
            csv_reader = csv.DictReader(self.tandemvault_tags_csv)
        except csv.Error:
            logging.error(
                '\n ERROR reading CSV: CSV does not have valid headers or is malformed.')
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
                continue

            synonyms = filter(None, [self.clean_tag_name(synonym) for synonym in json.loads(tandemvault_tag['synonym_names'])])

            tag, created = ImageTag.objects.get_or_create(name=name, source=self.source)
            if created:
                self.tags_created += 1
            else:
                self.tags_updated += 1

            # Remove existing Tandem Vault synonym relationships
            existing_synonyms = tag.synonyms.filter(source=self.source)
            if existing_synonyms:
                tag.synonyms.remove(*existing_synonyms)

            # Assign fresh Tandem Vault synonym relationships
            for synonym in synonyms:
                s, created = ImageTag.objects.get_or_create(name=synonym, source=self.source)
                tag.synonyms.add(s)

            tag.save()

    '''
    Sanitizes tag names
    '''
    def clean_tag_name(self, name):
        try:
            name = name.decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # we tried; make it behave
            name = unidecode(name)

        return name.lower().strip()

    '''
    Displays information about the import.
    '''
    def print_stats(self):
        stats = """
Finished import of Tandem Vault image tags.

Created: {0}
Updated: {1}
Deleted: {2}

Script executed in {3}
        """.format(
            self.tags_created,
            self.tags_updated,
            self.tags_deleted,
            self.exec_time
        )

        print(stats)

    '''
    Deletes ImageTags sourced from Tandem Vault
    that are not assigned to any Images.
    '''
    def delete_stale(self):
        stale_tags = ImageTag.objects.filter(images=None, source=self.source)

        self.tags_deleted = stale_tags.count()

        stale_tags.delete()
