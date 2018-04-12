from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import xml.etree.ElementTree as ET


class Command(BaseCommand):
    help = 'Imports catalog urls from the Acalog system'

    catalog_programs = []

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='The base url of the Acalog API'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='The api key used to connect to Acalog',
            dest='api-key',
            required=True
        )
        parser.add_argument(
            '--catalog-id',
            type=int,
            help='The ID of the catalog to use',
            dest='catalog-id',
            required=True
        )

    def handle(self, *args, **options):
        path = options['path']
        key = options['api-key']
        catalog_id = options['catalog-id']

        program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(path, key, catalog_id)

        # Fetch the catalog programs and set the variable
        self.get_catalog_programs(program_url)

        # Start matching up programs by name
        self.match_programs()

        return 0

    def get_catalog_programs(self, program_url):
        response = urllib2.urlopen(program_url)
        raw_data = response.read()
        program_root = ET.fromstring(raw_data)

        for result in program_root.iter('result'):
            self.catalog_programs.append(
                (
                    result.find('id').text, result.find('name').text
                )
            )

    def match_programs(self):
        programs = Program.objects.all()
        count = 0

        for id, name in self.catalog_programs:
            clean_name = self.strip_punctuation(name)

            try:
                program = programs.filter(name=clean_name)
            except Program.DoesNotExist:
                program=None

            for p in program:
                count = count + 1
                print p.name

        print count

    def strip_punctuation(self, value):
        retval = value.replace('.', '')

        return retval
