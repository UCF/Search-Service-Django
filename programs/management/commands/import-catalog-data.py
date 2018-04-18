from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import re
import itertools
import logging
from operator import attrgetter
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz


def clean_name(program_name):
    # Strip out punctuation
    name = program_name.replace('.', '')

    # Filter out stop words
    stop_words = [
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by',
        'for', 'from', 'has', 'he', 'in', 'is', 'it',
        'its', 'of', 'on', 'or', 'that', 'the', 'to', 'was',
        'were', 'will', 'with', 'degree', 'program', 'minor',
        'track', 'graduate', 'certificate', 'bachelor', 'master'
    ]

    name = ' '.join(filter(lambda x: x.lower() not in stop_words, name.split()))

    return name


class CatalogEntry(object):

    def __init__(self, id, name, program_type):
        self.id = id
        self.name = name
        self.type = program_type
        self.match_count = 0

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
        return clean_name(self.name)

    @property
    def has_matches(self):
        return self.match_count > 0


class MatchableProgram(object):

    def __init__(self, program):
        self.program = program
        self.matches = []

    @property
    def name_clean(self):
        return clean_name(self.program.name)

    @property
    def has_matches(self):
        return len(self.matches) > 0

    def get_best_match(self):
        if self.has_matches:
            return max(self.matches, key=attrgetter('match_score'))
        else:
            return None


class CatalogMatchEntry(object):
    def __init__(self, match_score, catalog_entry):
        self.match_score = match_score
        self.catalog_entry = catalog_entry


class Command(BaseCommand):
    help = 'Imports catalog urls from the Acalog system'

    catalog_programs = []

    ns = {
        'a': 'http://www.w3.org/2005/Atom',
        'h': 'http://www.w3.org/1999/xhtml'
    }

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
        parser.add_argument(
            '--verbose',
            help='Be verbose',
            action='store_const',
            dest='loglevel',
            const=logging.INFO,
            default=logging.WARNING,
            required=False
        )

    def handle(self, *args, **options):
        ET.register_namespace('a', 'http://www.w3.org/2005/Atom')
        ET.register_namespace('h', 'http://www.w3.org/1999/xhtml')


        self.path = options['path']
        self.key = options['api-key']
        self.catalog_id = options['catalog-id']
        self.catalog_url = options['catalog-url'] + 'preview/preview_program.php?catoid={0}&poid={1}'
        self.graduate = options['graduate']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(level=self.loglevel)

        program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(self.path, self.key, self.catalog_id)

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
        description_type, created = ProgramDescriptionType.objects.get_or_create(
            name='Catalog Description'
        )

        programs = Program.objects.all()
        match_count = 0
        career_name = ''

        if self.graduate:
            career_name = 'Graduate'
        else:
            career_name = 'Undergraduate'

        programs = programs.filter(career__name=career_name)

        for p in programs:
            # Wipe out existing catalog URL
            p.catalog_url = None
            p.save()

            p = MatchableProgram(p)
            filtered_entries = filter(lambda x: x.level == p.program.level, self.catalog_programs)

            for entry in filtered_entries:
                match_score = fuzz.token_sort_ratio(p.name_clean, entry.name_clean)
                if match_score > 75: # TODO allow threshold to be configurable somehow
                    p.matches.append(CatalogMatchEntry(match_score, entry))

            if p.has_matches:
                # Get the best match and update the program with the matched catalog URL
                match = p.get_best_match()
                matched_entry = match.catalog_entry
                p.program.catalog_url = self.catalog_url.format(self.catalog_id, matched_entry.id)
                p.program.save()

                # Update the program description with the description provided in the matched catalog entry
                try:
                    description = p.program.descriptions.get(profile_type=description_type)
                    description.description = self.get_description(matched_entry.id)
                    description.save()
                except ProgramDescription.DoesNotExist:
                    description = ProgramDescription(
                        profile_type=description_type,
                        description=self.get_description(matched_entry.id),
                        program=p.program
                    )
                    description.save()

                # Increment match counts for all programs and for the matched catalog entry
                match_count += 1
                matched_entry.match_count += 1

                logging.info(unicode('MATCH \n Matched program name: %s \n Cleaned program name: %s \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n Match score: %d \n' % (p.program.name, p.name_clean, matched_entry.name, matched_entry.name_clean, match.match_score)).encode('ascii', 'xmlcharrefreplace'))
            else:
                logging.info(unicode('FAILURE \n Matched program name: %s \n Cleaned program name: %s \n' % (p.program.name, p.name_clean)).encode('ascii', 'xmlcharrefreplace'))

        print 'Matched {0}/{1} of Existing {2} Programs to a Catalog Entry: {3:.0f}%'.format(match_count, len(programs), career_name, float(match_count) / float(len(programs)) * 100)
        print 'Matched {0}/{1} of Fetched Catalog Entries to at Least One Existing Program: {2:.0f}%'.format(len(filter(lambda x: x.has_matches == True, self.catalog_programs)), len(self.catalog_programs), len(filter(lambda x: x.has_matches == True, self.catalog_programs)) / float(len(self.catalog_programs)) * 100)


    def get_description(self, program_id):
        url = '{0}content?key={1}&format=xml&method=getItems&type=programs&ids[]={2}&catalog={3}'.format(
            self.path,
            self.key,
            program_id,
            self.catalog_id
        )

        response = urllib2.urlopen(url)
        raw_data = response.read()
        root = ET.fromstring(raw_data)

        content = root.find('.//a:content', self.ns )

        retval = ''

        for el in content:
            retval += ET.tostring(el, method='html')

        retval = retval.replace('<h:', '<').replace('</h:', '</')

        retval = retval.replace('xmlns:h="http://www.w3.org/1999/xhtml"', '')

        regex = re.compile(r'[\r\n\t]')

        retval = regex.sub(' ', retval)

        return retval
