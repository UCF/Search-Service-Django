from django.core.management.base import BaseCommand
from images.models import *

import logging


class Command(BaseCommand):
    help = 'Imports image assets from UCF\'s Tandem Vault instance.

    source         = 'Tandem Vault'
    modified       = timezone.now()
    images_created = 0
    images_updated = 0
    images_skipped = 0
    images_deleted = 0
    tags_created   = 0
    tags_updated   = 0
    tags_skipped   = 0
    tags_deleted   = 0

    def add_arguments(self, parser):
        # TODO allow date range or minimum date to be passed in?
        parser.add_argument(
            'path',
            type=str,
            help='The base url of the Tandem Vault API'
        ),
        parser.add_argument(
            '--assign_tags',
            type=bool,
            help='Set to True to pass all imported images to Azure\'s Computer Vision API to generate image tags.',
            dest='assign_tags',
            default=False,
            required=False
        )

    def handle(self, *args, **options):
        return

    def print_stats(self):
        stats = """
Finished import of Tandem Vault images.

Images
---------
Created: {0}
Updated: {1}
Skipped: {2}
Deleted: {3}

Image Tags
-------------
Created: {4}
Updated: {5}
Skipped: {6}
Deleted: {7}
        """.format(
            self.images_created,
            self.images_updated,
            self.images_skipped,
            self.images_deleted,
            self.tags_created,
            self.tags_updated,
            self.tags_skipped,
            self.tags_deleted
        )

        print(stats)

        return

    def delete_stale(self):
        stale_images = Image.objects.filter(
            modified__lt=self.modified,
            source=self.source
        )
        stale_tags = ImageTag.objects.filter(images=None)

        self.images_deleted = stale_images.count()
        self.tags_deleted = stale_tags.count()

        stale_images.delete()
        stale_tags.delete()

        return
