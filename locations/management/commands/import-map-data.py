from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.gis.geos import GEOSGeometry, LinearRing, Point, Polygon
from locations.models import *

from pathlib import Path
from io import BytesIO
import logging
import requests
import json
import sys


class Command(BaseCommand):
    help = 'Imports map.ucf.edu data from /locations.json JSON'

    processed = 0
    created = 0
    updated = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--map-data-types',
            type=str,
            dest='map_data_types',
            help='Comma-separated list of object_types from Map to be imported. Leave blank to import all.',
            required=False
        )

    def handle(self, *args, **options):
        logging.basicConfig(stream=sys.stdout, level=logging.WARNING)

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
            elif row['object_type'] == 'parkinglot':
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
        """.format(
            self.processed,
            self.created,
            self.updated
        )

        print(stats)

    def get_map_image(self, img_path):
        '''
        Fetches and returns a bytes object from map.ucf.edu
        for the img_path provided.
        '''
        photo = None

        if img_path:
            try:
                r = requests.get(f"https://map.ucf.edu/media/{img_path}")
                photo = BytesIO(r.content)
            except Exception as e:
                raise

        return photo

    def coords_to_point(self, point_coords):
        point = None

        if point_coords:
            try:
                # This is stupid, but, apparently coordinates that come from
                # Google Maps put lat/lng coordinates in the reverse order
                # that we expect. So, we must flip them here:
                point = Point([point_coords[1], point_coords[0]])
            except Exception as e:
                raise

        return point

    def coords_to_polygon(self, poly_coords):
        poly_list = []
        poly = None

        for linear_ring in poly_coords:
            # Make sure this linear ring isn't just a singular point.
            # Omit it if it doesn't look valid:
            if len(linear_ring) < 2:
                continue

            # Somehow some of our existing MapObj coord's don't
            # always start and end on the same coordinates.
            # Polygon generation fails if the provided start and
            # end coords aren't the same, so, try to rectify that here:
            if linear_ring[0] != linear_ring[-1]:
                linear_ring.append(linear_ring[0])

            poly_list.append(linear_ring)

        try:
            poly = GEOSGeometry(json.dumps({
                "type": "Polygon",
                "coordinates": poly_list
            }))
        except Exception:
            raise

        return poly

    def import_campus(self, row):
        pass

    def import_facility(self, row):
        photo = None
        try:
            photo = self.get_map_image(row['image'])
        except:
            logging.info('\n Could not download image from map.ucf.edu. Continuing anyway')

        point = None
        try:
            point = self.coords_to_point(row['googlemap_point'])
        except:
            logging.warning(f"Could not generate a point with coordinates provided for bldg ID {row['id']} ({row['name']}). Importing facility, but omitting point data.")


        poly = None
        if row['poly_coords']:
            # Try to catch multipolygons inappropriately stored
            # as polygons in Map.  TODO save these somehow?
            if len(row['poly_coords'][0]) == 1:
                logging.warning(f"Multipolygon coords provided for polygon for bldg ID {row['id']} ({row['name']}). Importing facility, but omitting polygon data.")
            else:
                try:
                    poly = self.coords_to_polygon(row['poly_coords'])
                except Exception as e:
                    logging.warning(f"Omitting polygon data--could not generate a polygon for bldg ID {row['id']} ({row['name']}): {e}")

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
                try:
                    existing_facility.photo.delete()
                except:
                    pass

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
        photo = None
        try:
            photo = self.get_map_image(row['image'])
        except:
            logging.info('\n Could not download image from map.ucf.edu. Continuing anyway')

        point = None
        try:
            point = self.coords_to_point(row['googlemap_point'])
        except:
            logging.warning(f"Could not generate a point with coordinates provided for bldg ID {row['id']} ({row['name']}). Importing parking lot, but omitting point data.")


        poly = None
        if row['poly_coords']:
            # Try to catch multipolygons inappropriately stored
            # as polygons in Map.  TODO save these somehow?
            if len(row['poly_coords'][0]) == 1:
                logging.warning(f"Multipolygon coords provided for polygon for bldg ID {row['id']} ({row['name']}). Importing parking lot, but omitting polygon data.")
            else:
                try:
                    poly = self.coords_to_polygon(row['poly_coords'])
                except Exception as e:
                    logging.warning(f"Omitting polygon data--could not generate a polygon for bldg ID {row['id']} ({row['name']}): {e}")

        try:
            existing_parkinglot = ParkingLot.objects.get(building_id=row['id'])
            existing_parkinglot.name = row['name']
            existing_parkinglot.building_id = row['id']
            existing_parkinglot.abbreviation = row['abbreviation']
            existing_parkinglot.description = row['profile']
            existing_parkinglot.point_coords = point
            existing_parkinglot.poly_coords = poly

            if photo:
                try:
                    existing_parkinglot.photo.delete()
                except:
                    pass

                existing_parkinglot.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            existing_parkinglot.save()

            self.updated += 1
        except ParkingLot.DoesNotExist:
            new_parkinglot = ParkingLot(
                name = row['name'],
                building_id = row['id'],
                abbreviation = row['abbreviation'],
                description = row['profile'],
                point_coords = point,
                poly_coords = poly
            )

            if photo:
                new_parkinglot.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            new_parkinglot.save()

            self.created += 1

        self.processed += 1

    def import_location(self, row):
        photo = None
        try:
            photo = self.get_map_image(row['image'])
        except:
            logging.info('\n Could not download image from map.ucf.edu. Continuing anyway')

        point = None
        try:
            point = self.coords_to_point(row['googlemap_point'])
        except:
            logging.warning(f"Could not generate a point with coordinates provided for bldg ID {row['id']} ({row['name']}). Importing facility, but omitting point data.")


        poly = None
        if row['poly_coords']:
            # Try to catch multipolygons inappropriately stored
            # as polygons in Map.  TODO save these somehow?
            if len(row['poly_coords'][0]) == 1:
                logging.warning(f"Multipolygon coords provided for polygon for bldg ID {row['id']} ({row['name']}). Importing facility, but omitting polygon data.")
            else:
                try:
                    poly = self.coords_to_polygon(row['poly_coords'])
                except Exception as e:
                    logging.warning(f"Omitting polygon data--could not generate a polygon for bldg ID {row['id']} ({row['name']}): {e}")

        dining_location = LocationType.objects.get(name='Dining')

        try:
            existing_location = Location.objects.get(import_id=row['id'])
            existing_location.name = row['name']
            existing_location.import_id = row['id']
            existing_location.description = row['profile']
            existing_location.location_type = dining_location
            existing_location.profile_url = row['profile_link']
            existing_location.point_coords = point
            existing_location.poly_coords = poly

            if photo:
                try:
                    existing_location.photo.delete()
                except:
                    pass

                existing_location.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            existing_location.save()

            self.updated += 1
        except Location.DoesNotExist:
            new_location = Location(
                name = row['name'],
                import_id = row['id'],
                description = row['profile'],
                location_type = dining_location,
                profile_url = row['profile_link'],
                point_coords = point,
                poly_coords = poly
            )

            if photo:
                new_location.photo.save(
                    name=Path(row['image']).name,
                    content=File(photo),
                    save=False
                )

            new_location.save()

            self.created += 1

        self.processed += 1

    def import_point_of_interest(self, row):
        pass
