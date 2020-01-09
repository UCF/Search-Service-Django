from django.core.management.base import BaseCommand
from images.models import *

import logging
import timeit
import datetime

import requests
from progress.bar import Bar


class Command(BaseCommand):
    help = 'Imports all existing image tags from UCF\'s Tandem Vault instance.'

    progress_bar = Bar('Processing')
    source       = 'Tandem Vault'
    tags_created = 0
    tags_updated = 0
    tags_deleted = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--tandemvault-tags-csv-url',
            type=str,
            help='URL that points to a CSV containing existing tag and synonym information from Tandem Vault',
            dest='tandemvault-tags-csv-url',
            required=True
        )

    def handle(self, *args, **options):
        self.tandemvault_tags_csv = options['tandemvault-tags-csv-url']

        # Start a timer for the bulk of the script
        self.exec_time = 0
        self.exec_start = timeit.default_timer()

        # Process the CSV
        self.load_tandemvault_tags()

        # Delete stale Tandem Vault image tags
        self.delete_stale()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(seconds=self.exec_end - self.exec_start)

        # Print the results
        self.progress_bar.finish()
        self.print_stats()

        return

    '''
    Pre-load a CSV of Tandem Vault tags + synonyms.

    TODO
    '''
    def load_tandemvault_tags():
        pass

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
    Deletes Image objects sourced from Tandem Vault that are no
    longer present in Tandem Vault, and deletes ImageTags sources
    from Tandem Vault that are not assigned to any Images.
    '''
    def delete_stale(self):
        stale_tags = ImageTag.objects.filter(images=None, source=self.source)

        self.tags_deleted = stale_tags.count()

        stale_tags.delete()
