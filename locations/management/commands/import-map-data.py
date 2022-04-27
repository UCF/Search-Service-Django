from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.gis.geos import GEOSGeometry, LinearRing, Point, Polygon
from locations.models import *

from pathlib import Path
from io import BytesIO
import logging
import requests
import json


class Command(BaseCommand):
    help = 'Imports map.ucf.edu data from /locations.json JSON'

    processed = 0
    created = 0
    updated = 0
    skipped = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--map-data-types',
            type=str,
            dest='map_data_types',
            help='Comma-separated list of object_types from Map to be imported. Leave blank to import all.',
            required=False
        )

    def handle(self, *args, **options):
        data_types = options['map_data_types']
        r = requests.get(f"https://map.ucf.edu/locations.json?types={data_types}")
        data = r.json()

        self.do_import(data)
        self.print_stats()

    def do_import(self, data):
        for row in data:
            if row['object_type'] in ['location', 'regionalcampus']:
                self.import_campus(row)
            elif row['object_type'] == 'building':
                self.import_facility(row)
            elif row['object_type'] == 'parking':
                self.import_parking_lot(row)
            elif row['object_type'] == 'dininglocation':
                self.import_location(row)
            else:
                self.import_point_of_interest(row)


    def print_stats(self):
        stats = """
All Finished Importing!
-----------------------

Processed: {0}
Created:   {1}
Updated:   {2}
Skipped:   {3}
        """.format(
            self.processed,
            self.created,
            self.updated,
            self.skipped
        )

        print(stats)

    def import_campus(self, row):
        pass

    def import_facility(self, row):
        photo = None
        if row['image']:
            try:
                r = requests.get(f"https://map.ucf.edu/media/{row['image']}")
                photo = BytesIO(r.content)
            except Exception as e:
                logging.info('\n Could not download image from map.ucf.edu. Continuing anyway')

        point = None
        if row['googlemap_point']:
            try:
                # This is stupid, but, apparently coordinates that come from
                # Google Maps put lat/lng coordinates in the reverse order
                # that we expect. So, we must flip them here:
                point = GEOSGeometry(json.dumps({
                    "type": "Point",
                    "coordinates": [row['googlemap_point'][1], row['googlemap_point'][0]]
                }))
            except Exception as e:
                print(f"Error while importing facility with bldg ID {row['id']} ({row['name']}): {e}")
                self.skipped += 1
                return

        poly = None
        if row['poly_coords']:
            # Try to catch multipolygons inappropriately stored
            # as polygons in Map.  TODO save these somehow?
            if len(row['poly_coords'][0]) == 1:
                print(f"Multipolygon coords provided for polygon for bldg ID {row['id']} ({row['name']}). Importing facility, but omitting polygon data.")
            else:
                # Somehow some of our existing MapObj coord's don't
                # always start and end on the same coordinates.
                # Polygon generation fails if the provided start and
                # end coords aren't the same, so, try to rectify that here:
                poly_list = []

                for linear_ring in row['poly_coords']:
                    if linear_ring[0] != linear_ring[-1]:
                        linear_ring.append(linear_ring[0])

                    poly_list.append(linear_ring)

                try:
                    poly = GEOSGeometry(json.dumps({
                        "type": "Polygon",
                        "coordinates": poly_list
                    }))
                except Exception as e:
                    print(f"Error while importing facility with bldg ID {row['id']} ({row['name']}): {e}")
                    self.skipped += 1
                    return

        try:
            existing_facility = Facility.objects.get(building_id=row['id'])
            existing_facility.name = row['name']
            existing_facility.building_id = row['id']
            existing_facility.abbreviation = row['abbreviation']
            existing_facility.description = row['profile']
            existing_facility.profile_url = row['profile_link']
            existing_facility.point_coords = point
            existing_facility.poly_coords = poly

            if photo:
                existing_facility.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            existing_facility.save()

            self.updated += 1
        except Facility.DoesNotExist:
            new_facility = Facility(
                name = row['name'],
                building_id = row['id'],
                abbreviation = row['abbreviation'],
                description = row['profile'],
                profile_url = row['profile_link'],
                point_coords = point,
                poly_coords = poly
            )

            if photo:
                new_facility.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            new_facility.save()

            self.created += 1

        self.processed += 1

    def import_parking_lot(self, row):
        pass

    def import_location(self, row):
        pass

    def import_point_of_interest(self, row):
        pass
