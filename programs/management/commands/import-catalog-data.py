from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import re
import itertools
from operator import attrgetter
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz


class CatalogEntry(object):


    def __init__(self, id, name, program_type):
        self.id = id
        self.name = name
        self.type = program_type
        self.matches = []

    @property
    def level(self):
        try:
            temp_level = Level.objects.get(name=self.type)
            return temp_level
        except Level.DoesNotExist:
            temp_level = None

        if self.type in ['Major', 'Accelerated Undergraduate-Graduate Program']:
            return Level.objects.get(name='Bachelors')
        elif self.type == 'Certificate':
            return Level.objects.get(name='Certificate')
        elif self.type == 'Minor':
            return Level.objects.get(name='None')
        elif self.type in ['Master', 'Master of Fine Arts']:
            return Level.objects.get(name='Masters')
        else:
            return Level.objects.get(name='Bachelors')

    @property
    def name_clean(self):
        stop_words = [
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by',
            'for', 'from', 'has', 'he', 'in', 'is', 'it',
            'its', 'of', 'on', 'or', 'that', 'the', 'to', 'was',
            'were', 'will', 'with', 'degree', 'program', 'minor',
            'track', 'graduate', 'certificate'
        ]

        name = ' '.join(filter(lambda x: x.lower() not in stop_words, self.name.split()))
        name = name.replace('.', '')
        return name

    @property
    def has_matches(self):
        return len(self.matches) > 0

    def get_best_match(self):
        if self.has_matches:
            return max(self.matches, key=attrgetter('match_score'))
        else:
            return None


class CatalogMatchEntry(object):
    def __init__(self, match_score, program):
        self.match_score = match_score
        self.program = program


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
        parser.add_argument(
            '--graduate',
            type=bool,
            help='Set to True if this is the graduate import',
            dest='graduate',
            default=False,
            required=False
        )

    def handle(self, *args, **options):
        path = options['path']
        key = options['api-key']
        self.catalog_id = options['catalog-id']
        self.catalog_url = options['catalog-url'] + 'preview/preview_program.php?catoid={0}&poid={1}'
        self.graduate = options['graduate']

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
                        result.find('name').text.encode('ascii', 'ignore'),
                        result.find('type').text.encode('ascii', 'ignore')
                    )
                )

    def match_programs(self):
        programs = Program.objects.all()

        if self.graduate:
            programs = programs.filter(career__name='Graduate')

        for entry in self.catalog_programs:
            for p in programs.filter(level=entry.level):
                match_score = fuzz.token_sort_ratio(p.name, entry.name_clean)
                if match_score > 75: # TODO allow threshold to be configurable somehow
                    entry.matches.append(CatalogMatchEntry(match_score, p))

            if entry.has_matches:
                match = entry.get_best_match()
                matched_program = match.program
                matched_program.catalog_url = self.catalog_url.format(self.catalog_id, entry.id)
                matched_program.save()
                #print 'MATCH \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n Matched program name: %s \n Match score: %d \n' % (entry.name, entry.name_clean, matched_program.name, match.match_score)
            #else:
                #print 'FAILURE \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n' % (entry.name, entry.name_clean)


        match_count = len([x for x in self.catalog_programs if x.has_matches == True])

        print 'Matched {0}/{1} of Catalog Programs: {2:.0f}%'.format(match_count, len(self.catalog_programs), float(match_count) / float(len(self.catalog_programs)) * 100)
