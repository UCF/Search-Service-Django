from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import re
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
        parser.add_argument(
            '--catalog-url',
            type=str,
            help='The url to use when building catalog urls',
            dest='catalog-url',
            required=True
        )

    def handle(self, *args, **options):
        path = options['path']
        key = options['api-key']
        self.catalog_id = options['catalog-id']
        self.catalog_url = options['catalog-url'] + 'preview/preview_program.php?catoid={0}&poid={1}'

        program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(path, key, self.catalog_id)

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

        print len(self.catalog_programs)

    def match_programs(self):
        programs = Program.objects.all()
        count = 0

        for id, name in self.catalog_programs:
            # Attempt exact match first
            clean_name = self.strip_punctuation(name)

            try:
                program = programs.get(name=clean_name)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                print 'Attempt 1 successful: {0}'.format(clean_name)
                # Match was found, so continue with loop
                continue
            except Program.MultipleObjectsReturned:
                print 'Attempt 1 failed: {0} - Reason: MultipleObjectsReturned'.format(clean_name)
            except Program.DoesNotExist:
                print 'Attempt 1 failed: {0} - Reason: DoesNotExist'.format(clean_name)
                program=None



            # Attempt match with degree removed
            clean_name = self.strip_degree(name)

            try:
                program = programs.get(name=clean_name)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                print 'Attempt 2 successful: {0}'.format(clean_name)
                continue
            except Program.MultipleObjectsReturned:
                print 'Attempt 2 failed: {0} - Reason: MultipleObjectsReturned'.format(clean_name)
            except Program.DoesNotExist:
                print 'Attempt 2 failed: {0} - Reason: DoesNotExist'.format(clean_name)
                program=None

            # Attempt match for minors
            clean_name = self.strip_minor(name)

            try:
                minor = Degree.objects.get(name='MIN')
                program = programs.get(name=clean_name, degree=minor)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                print 'Attempt 3 successful: {0}'.format(clean_name)
                continue
            except Program.MultipleObjectsReturned:
                print 'Attempt 3 failed: {0} - Reason: MultipleObjectsReturned'.format(clean_name)
            except Program.DoesNotExist:
                print 'Attempt 3 failed: {0} - Reason: DoesNotExist'.format(clean_name)
                program=None

        print count

    def strip_minor(self, value):
        retval = re.sub('\ Minor', '', value)

        return retval

    def strip_degree(self, value):
        # Remove degree name entirely from string
        retval = re.sub('\(.*\)', '', value).strip()

        return retval

    def strip_punctuation(self, value):
        retval = value.replace('.', '')

        return retval
