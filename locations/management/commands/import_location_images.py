# -*- coding: utf-8 -*-
"""
Management command to backfill images on existing Location records by
matching against the UCF map API using the abbreviation field.

For each local record with an abbreviation, the command looks up a
record in the map API feed with the same abbreviation, downloads the
image, and saves it to the Location's ImageField (local or S3
depending on settings.USE_S3).

Usage:
    python manage.py import_location_images
    python manage.py import_location_images --overwrite
    python manage.py import_location_images --dry-run
"""
import os

import requests

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from locations.models import Location


DEFAULT_ENDPOINT = 'https://map.ucf.edu/locations.json'
IMAGE_BASE_URL = 'https://map.ucf.edu/media/'


class Command(BaseCommand):
    help = 'Backfill images from the UCF map API by matching on abbreviation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            dest='url',
            default=DEFAULT_ENDPOINT,
            help='URL of the locations JSON feed. Default: {}'.format(DEFAULT_ENDPOINT)
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Overwrite existing image values. By default only blank images are filled.'
        )
        parser.add_argument(
            '--image-base-url',
            dest='image_base_url',
            default=IMAGE_BASE_URL,
            help='Base URL prepended to relative image paths from the feed. Default: {}'.format(IMAGE_BASE_URL)
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Report what would be updated without saving.'
        )

    def handle(self, *args, **options):
        url = options['url']
        overwrite = options['overwrite']
        dry_run = options['dry_run']
        image_base_url = options['image_base_url'].rstrip('/')

        self.stdout.write('Fetching {}'.format(url))

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise CommandError('Failed to fetch {}: {}'.format(url, e))
        except ValueError as e:
            raise CommandError('Could not parse JSON from {}: {}'.format(url, e))

        if not isinstance(data, list):
            raise CommandError('Expected a JSON array from the endpoint.')

        # Build a lookup dict from abbreviation → image.
        # Abbreviations are lowercased for case-insensitive matching.
        # Where multiple API records share an abbreviation, the last
        # non-empty image wins.
        api_images = {}
        for record in data:
            abbr = (record.get('abbreviation') or '').strip().lower()
            image = (record.get('image') or '').strip()
            if abbr and image:
                # Construct the full URL if the path is relative
                if not image.startswith(('http://', 'https://')):
                    image = '{}/{}'.format(image_base_url, image.lstrip('/'))
                api_images[abbr] = image

        self.stdout.write(
            'Built image map from {} API records ({} with abbreviation+image).'.format(
                len(data), len(api_images)
            )
        )

        # Fetch local records that have an abbreviation.
        local_qs = Location.objects.exclude(abbreviation__isnull=True).exclude(abbreviation='')
        self.stdout.write('Checking {} local records with an abbreviation...'.format(
            local_qs.count()
        ))

        updated = 0
        skipped_no_match = 0
        skipped_has_image = 0

        for location in local_qs.iterator():
            abbr_key = location.abbreviation.strip().lower()
            api_image = api_images.get(abbr_key)

            if not api_image:
                skipped_no_match += 1
                continue

            if location.image and not overwrite:
                skipped_has_image += 1
                continue

            if dry_run:
                self.stdout.write('Would update: {} [{}] image={}'.format(
                    location.name or location.pk, location.abbreviation, api_image
                ))
                updated += 1
                continue

            # Download the image and save it through the ImageField so the
            # correct storage backend (S3 or local) handles the file.
            try:
                img_response = requests.get(api_image, timeout=15)
                img_response.raise_for_status()
            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(
                    'Failed to download image for {} [{}]: {}'.format(
                        location.name or location.pk, location.abbreviation, e
                    )
                ))
                continue

            filename = os.path.basename(api_image.rstrip('/').split('?')[0])
            if not filename:
                filename = 'location_{}.jpg'.format(location.pk)

            location.image.save(filename, ContentFile(img_response.content), save=True)
            updated += 1

        action = 'Would update' if dry_run else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            '{} {} record(s). '
            'Skipped {} (no API match), {} (already had image).'.format(
                action, updated, skipped_no_match, skipped_has_image
            )
        ))
