from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import re
import itertools
import xml.etree.ElementTree as ET


class CatalogEntry(object):


    def __init__(self, id, name, program_type):
        self.id = id
        self.name = name
        self.type = program_type

    @property
    def level(self):
        if self.type in ['Major', 'Accelerated Undergraduate-Graduate Program']:
            return Level.objects.get(name='Bachelors')
        elif self.type == 'Certificate':
            return Level.objects.get(name='Certificate')
        elif self.type == 'Minor':
            return Level.objects.get(name='None')
        else:
            return Level.objects.get(name='Bachelors')

    def remove_stop_words(self, title):
        stop_words = [
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by',
            'for', 'from', 'has', 'he', 'in', 'is', 'it',
            'its', 'of', 'on', 'that', 'the', 'to', 'was',
            'were', 'will', 'with', 'degree', 'program', 'minor'
        ]

        return ' '.join(filter(lambda x: x.lower() not in stop_words, title.split()))

    def is_match(self, title, level, threshold):
        """
        Finds matches for each unique word in the name
        and returns count
        """
        test_value = self.remove_stop_words(re.sub('[^a-z0-9 ]', '', title.lower()))
        test_case = self.remove_stop_words(re.sub('[^a-z0-9 ]', '', self.name.lower()))

        split_value = test_value.split(' ')
        word_count = len(test_case.split(' '))

        match_count = 0

        for v in split_value:
            test = r"\b{0}\b".format(v)
            matches = re.search(test, test_case)
            if matches:
                match_count += 1

        if float(match_count) / float(word_count) * 100 >= threshold:
            if level == self.level:
                print "Value: {0} - Case: {1} - Score: {2:.0f}".format(test_value, test_case, float(match_count) / float(word_count) * 100)
                return True

        return False


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
            if result.find('type') is not None:
                self.catalog_programs.append(
                    CatalogEntry(
                        result.find('id').text,
                        result.find('name').text,
                        result.find('type').text
                    )
                )

    def match_programs(self):
        programs = Program.objects.all()
        count = 0

        for entry in self.catalog_programs:

            # Attempt exact match first
            clean_name = self.strip_punctuation(entry.name)

            try:
                program = programs.get(name__iexact=clean_name, level=entry.level)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                # Match was found, so continue with loop
                continue
            except Program.MultipleObjectsReturned:
                program=None
            except Program.DoesNotExist:
                program=None



            # Attempt match with degree removed
            clean_name = self.strip_degree(entry.name)

            try:
                program = programs.get(name__iexact=clean_name, level=entry.level)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                # print 'Attempt 2 successful: {0}'.format(clean_name)
                continue
            except Program.MultipleObjectsReturned:
                program=None
            except Program.DoesNotExist:
                program=None

            # Attempt match for minors
            clean_name = self.strip_minor(entry.name)

            try:
                minor = Degree.objects.get(name='MIN')
                program = programs.get(name__iexact=clean_name, degree=minor)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                continue
            except Program.MultipleObjectsReturned:
                program=None
            except Program.DoesNotExist:
                program=None


            # Attempt a match using classic_clean
            clean_name = self.classic_clean(entry.name)

            names = set(p for p in programs)

            try:
                program = next(x for x in names if self.classic_clean(x.name) == clean_name)
                program.catalog_url = self.catalog_url.format(self.catalog_id, id)
                program.save()
                count += 1
                continue
            except StopIteration:
                program=None


            # Attempt to get best match with regex
            for p in programs:
                match = entry.is_match(p.name, p.level, 75)
                if match:
                    print "Program: {0} == Entry: {1}".format(p.name, entry.name)
                    p.catalog_url = self.catalog_url.format(self.catalog_id, id)
                    p.save()
                    count += 1
                    continue


        print 'Matched {0}/{1} of Programs: {2:.0f}%'.format(count, len(self.catalog_programs), float(count) / float(len(self.catalog_programs)) * 100)

    def classic_clean(self, value):
        retval = self.strip_degree(value)
        retval = retval.lower()
        retval = re.sub('degree', '', retval)
        retval = re.sub('program', '', retval)
        retval = re.sub('[^a-z0-9]', '', retval)

        return retval

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
