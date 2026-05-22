# -*- coding: utf-8 -*-
"""
Management command to import all locations from the UCF map API.

The feed at map.ucf.edu/locations.json is the authoritative legacy source.
Each record is keyed by its `id` field, stored as `location_id` on the model.

Usage:
    python manage.py import_map_locations
    python manage.py import_map_locations --url https://map.ucf.edu/locations.json
    python manage.py import_map_locations --dry-run
"""
import json
from datetime import datetime

import requests

from django.core.management.base import BaseCommand, CommandError

from locations.models import Location


DEFAULT_ENDPOINT = 'https://map.ucf.edu/locations.json'


class Command(BaseCommand):
    help = 'Import all locations from the UCF map API (map.ucf.edu/locations.json).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            dest='url',
            default=DEFAULT_ENDPOINT,
            help='URL of the locations JSON feed. Default: {}'.format(DEFAULT_ENDPOINT)
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Parse the feed and report what would be imported without saving.'
        )

    def handle(self, *args, **options):
        url = options['url']
        dry_run = options['dry_run']

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
            raise CommandError('Expected a JSON array from the endpoint, got {}.'.format(
                type(data).__name__
            ))

        self.stdout.write('Processing {} records...'.format(len(data)))

        created = 0
        updated = 0
        skipped = 0
        seen_ids = set()

        for record in data:
            location_id = record.get('id')
            if not location_id:
                skipped += 1
                continue

            location_id = str(location_id)
            seen_ids.add(location_id)

            # Coordinates: API provides [lat, lng] lists or null
            gmap = record.get('googlemap_point')
            googlemap_lat = gmap[0] if gmap and len(gmap) >= 2 else None
            googlemap_lng = gmap[1] if gmap and len(gmap) >= 2 else None

            imap = record.get('illustrated_point')
            illustrated_lat = imap[0] if imap and len(imap) >= 2 else None
            illustrated_lng = imap[1] if imap and len(imap) >= 2 else None

            # poly_coords: API provides a nested array or null; store as JSON string
            poly_coords_raw = record.get('poly_coords')
            poly_coords = json.dumps(poly_coords_raw) if poly_coords_raw is not None else None

            # modified: parse "YYYY-MM-DD HH:MM:SS" string
            modified = None
            modified_str = record.get('modified')
            if modified_str:
                try:
                    modified = datetime.strptime(modified_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass

            # image: convert empty string to None for cleanliness
            image = record.get('image') or None

            defaults = {
                'name': record.get('name'),
                'description': record.get('description'),
                'profile': record.get('profile'),
                'profile_link': record.get('profile_link'),
                'abbreviation': record.get('abbreviation'),
                'image': image,
                'object_type': record.get('object_type'),
                'googlemap_lat': googlemap_lat,
                'googlemap_lng': googlemap_lng,
                'illustrated_lat': illustrated_lat,
                'illustrated_lng': illustrated_lng,
                'poly_coords': poly_coords,
                'modified': modified,
            }

            if dry_run:
                label = record.get('name') or record.get('description') or location_id
                self.stdout.write('Would import: {} [{}] ({})'.format(
                    label, location_id, record.get('object_type', '')
                ))
                continue

            obj, was_created = Location.objects.update_or_create(
                location_id=location_id,
                defaults=defaults
            )

            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'Dry run complete. {} records found, {} skipped (no id).'.format(
                    len(seen_ids), skipped
                )
            ))
            return

        # Remove map-API-sourced records no longer present in the feed.
        # Records that also have an import_key came from Excel and are left alone.
        stale_qs = Location.objects.filter(
            location_id__isnull=False,
            import_key__isnull=True
        ).exclude(location_id__in=seen_ids)
        deleted, _ = stale_qs.delete()

        self.stdout.write(self.style.SUCCESS(
            'Import complete. Created: {}, Updated: {}, Deleted: {}, Skipped: {}.'.format(
                created, updated, deleted, skipped
            )
        ))
