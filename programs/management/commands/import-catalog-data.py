from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import requests
import re
import itertools
import logging
import sys
from operator import attrgetter
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup, NavigableString


def clean_name(program_name):
    name = program_name

    # Ensure we're working with a str object, not bytes:
    if type(name) is bytes:
        name = name.decode()

    # Strip out punctuation
    name = name.replace('.', '')

    # Fix miscellaneous inconsistencies
    name = name.replace('Nonthesis', 'Non-Thesis')
    name = name.replace('Bachelor of Design', '')
    name = name.replace('In State', 'In-State')
    name = name.replace('Out of State', 'Out-of-State')
    name = name.replace('Accel', 'Accelerated')

    # Filter out case-sensitive stop words
    stop_words_cs = [
        'as'
    ]
    name = ' '.join([x for x in name.split() if x not in stop_words_cs])

    # Filter out case-insensitive stop words
    stop_words_ci = [
        'a', 'an', 'and', 'are', 'at', 'be', 'by',
        'for', 'from', 'has', 'he', 'in', 'is', 'it',
        'its', 'of', 'on', 'or', 'that', 'the', 'to', 'was',
        'were', 'will', 'with', 'degree', 'program', 'minor',
        'track', 'graduate', 'certificate', 'bachelor', 'master',
        'doctor', 'online', 'ucf'
    ]
    name = ' '.join([x for x in name.split() if x.lower() not in stop_words_ci])

    return name


class CatalogEntry(object):

    def __init__(self, id, name, program_type):
        self.id = id
        self.name = name.decode()
        self.type = program_type.decode()
        self.match_count = 0

    @property
    def level(self):
        try:
            temp_level = Level.objects.get(name=self.type)
            return temp_level
        except Level.DoesNotExist:
            temp_level = None

        if self.type in ['Major', 'Accelerated Undergraduate-Graduate Program', 'Articulated A.S. Programs']:
            return Level.objects.get(name='Bachelors')
        elif self.type == 'Certificate':
            return Level.objects.get(name='Certificate')
        elif self.type == 'Minor':
            return Level.objects.get(name='None')
        elif self.type in ['Master', 'Master of Fine Arts']:
            return Level.objects.get(name='Masters')

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
        self.catalog_url = options['catalog-url'] + '/preview_program.php?catoid={0}&poid={1}'
        self.graduate = options['graduate']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(self.path, self.key, self.catalog_id)

        # Fetch the catalog programs and set the variable
        self.get_catalog_programs(program_url)

        # Start matching up programs by name
        self.match_programs()

        return 0

    def get_catalog_programs(self, program_url):
        response = requests.get(program_url)
        encoding = response.encoding
        raw_data = response.text.encode(encoding)
        program_root = ET.fromstring(raw_data)

        for result in program_root.iter('result'):
            if result.find('type') is not None and result.find('state').find('code').text == '1':
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
        description_type_full, created = ProgramDescriptionType.objects.get_or_create(
            name='Full Catalog Description'
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

            # Wipe out existing catalog descriptions
            try:
                description = p.descriptions.get(description_type=description_type)
                description.delete()
            except ProgramDescription.DoesNotExist:
                pass
            try:
                description_full = p.descriptions.get(description_type=description_type_full)
                description_full.delete()
            except ProgramDescription.DoesNotExist:
                pass

            p = MatchableProgram(p)
            filtered_entries = [x for x in self.catalog_programs if x.level == p.program.level]

            for entry in filtered_entries:
                match_score = fuzz.token_sort_ratio(p.name_clean, entry.name_clean)
                if match_score >= self.get_match_threshold(p, entry):
                    p.matches.append(CatalogMatchEntry(match_score, entry))

            if p.has_matches:
                # Get the best match and update the program with the matched catalog URL
                match = p.get_best_match()
                matched_entry = match.catalog_entry
                p.program.catalog_url = self.catalog_url.format(self.catalog_id, matched_entry.id)
                p.program.save()

                # Create new program descriptions with the description provided in the matched catalog entry
                description = ProgramDescription(
                    description_type=description_type,
                    description=self.get_description(matched_entry.id),
                    program=p.program
                )
                description.save()

                description_full = ProgramDescription(
                    description_type=description_type_full,
                    description=self.get_description_full(
                        matched_entry.id,
                        p.program.catalog_url
                    ),
                    program=p.program
                )
                description_full.save()

                # Increment match counts for all programs and for the matched catalog entry
                match_count += 1
                matched_entry.match_count += 1

                logging.info(str('MATCH \n Matched program name: %s \n Cleaned program name: %s \n Catalog entry full name: %s \n Cleaned catalog entry name: %s \n Match score: %d \n' % (p.program.name, p.name_clean, matched_entry.name, matched_entry.name_clean, match.match_score)).encode('ascii', 'xmlcharrefreplace'))
            else:
                logging.info(str('FAILURE \n Matched program name: %s \n Cleaned program name: %s \n' % (p.program.name, p.name_clean)).encode('ascii', 'xmlcharrefreplace'))

        print('Matched {0}/{1} of Existing {2} Programs to a Catalog Entry: {3:.0f}%'.format(match_count, len(programs), career_name, float(match_count) / float(len(programs)) * 100))
        print('Matched {0}/{1} of Fetched Catalog Entries to at Least One Existing Program: {2:.0f}%'.format(len([x for x in self.catalog_programs if x.has_matches == True]), len(self.catalog_programs), len([x for x in self.catalog_programs if x.has_matches == True]) / float(len(self.catalog_programs)) * 100))


    def get_description(self, program_id):
        url = '{0}content?key={1}&format=xml&method=getItems&type=programs&ids[]={2}&catalog={3}'.format(
            self.path,
            self.key,
            program_id,
            self.catalog_id
        )

        response = requests.get(url)
        encoding = response.encoding
        raw_data = response.text.encode(encoding)

        # Strip xmlns attributes to parse string to xml without namespaces
        data = re.sub(b' xmlns(?:\:[a-z]*)?="[^"]+"', b'', raw_data)
        root = BeautifulSoup(data, 'xml')
        if self.graduate:
            cores = root.find('cores')
            description_xml = cores.find('core').encode_contents()
            description_html = BeautifulSoup(description_xml, 'html.parser')
        else:
            description_xml = root.find('content').encode_contents()
            description_html = BeautifulSoup(description_xml, 'html.parser')

        tag_whitelist = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'pre',
            'table', 'tbody', 'thead', 'tr', 'td', 'a',
            'ul', 'li', 'ol',
            'b', 'em', 'i', 'strong', 'u'
        ]

        # Filter out tags not in our whitelist (replace them with span's)
        for match in description_html.descendants:
            if match.name not in tag_whitelist and isinstance(match, NavigableString) == False:
                match.name = 'span'
                match.attrs = []

        # BS seems to have a hard time with doing this in-place, so perform
        # a second loop to remove the garbage tags
        for span_match in description_html.find_all('span'):
            span_match.unwrap()

        # Strip newlines
        nl_regex = re.compile(r'[\r\n\t]')
        description_html = nl_regex.sub(' ', str(description_html))

        description_html = re.sub(r'[\x01-\x1F\x7F]', '', description_html)
        # Final filter out of Program Description
        description_html = re.sub('Program Description<a name=\"ProgramDescription\"></a><a id=\"core-\d+\" name=\"programdescription\"></a>', '', description_html)
        description_html = re.sub('1Active-Visible.*', '', description_html)

        return description_html

    def get_description_full(self, program_id, catalog_url):
        response = requests.get(catalog_url)
        encoding = response.encoding
        raw_data = response.text.encode(encoding)

        root = BeautifulSoup(raw_data, 'html.parser')

        description_str = ''
        desc_parts = root.select('.block_content > .table_default > tr')
        desc_1_row = desc_parts[0]
        desc_2_row = desc_parts[1]

        # Parse first part of description, which is basically
        # everything up to course listings/plans of study.
        # Ignore table nodes in this row (assume they're just
        # contact info):
        for desc_1_node in desc_1_row.find(class_='table_default').next_siblings:
            if isinstance(desc_1_node, NavigableString) == False and desc_1_node.name != 'table':
                description_str += str(desc_1_node)

        # Parse second description part:
        for desc_2_node in desc_2_row.td:
            if isinstance(desc_2_node, NavigableString) == False:
                description_str += str(desc_2_node)

        # Translate description_str into soup:
        description_html = BeautifulSoup(description_str, 'html.parser')

        tag_whitelist = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'pre',
            'table', 'tbody', 'thead', 'tr', 'td',
            'ul', 'li', 'ol',
            'b', 'em', 'i', 'strong', 'u'
        ]

        for match in description_html.descendants:
            if isinstance(match, NavigableString) == False:
                if match.name not in tag_whitelist:
                    # Filter out tags not in our whitelist (replace them with span's)
                    match.name = 'span'
                    match.attrs = []
                else:
                    # Remove unused attrs from elements
                    if 'class' in match.attrs:
                        match.attrs.pop('class')


        # BS seems to have a hard time with doing this in-place, so perform
        # a second loop to remove the garbage tags
        for span_match in description_html.find_all('span'):
            span_match.unwrap()

        # Strip newlines
        nl_regex = re.compile(r'[\r\n\t]')
        description_html = nl_regex.sub(' ', str(description_html))

        description_html = re.sub(r'[\x01-\x1F\x7F]', '', description_html)
        # Final filter out of Program Description
        description_html = re.sub('1Active-Visible.*', '', description_html)

        return description_html

    def get_match_threshold(self, matchable_program, entry):
        # Base threshold score value. Increase base threshold
        # for graduate programs.
        threshold = 80
        if matchable_program.program.career.name == 'Graduate':
            threshold = 85

        # Determine the mean (average) number of words between the
        # existing program name and catalog entry name
        word_count_mp = len(matchable_program.name_clean.split())
        word_count_e = len(entry.name_clean.split())
        word_counts = [word_count_mp, word_count_e]
        word_count_mean = float(sum(word_counts)) / max(len(word_counts), 1)

        # Enforce a stricter threshold between program names with a lower
        # mean word count
        if word_count_mean <= 3:
            threshold += 2

        if word_count_mean <= 2:
            threshold += 3

        # Enforce stricter threshold for subplans, since they have a decent
        # chance of unintentionally matching against their parent program when
        # they shouldn't
        if matchable_program.program.is_subplan:
            threshold = 90

        # Reduce the threshold for accelerated undergraduate programs, since
        # their names tend to vary more greatly between the catalog and
        # our data
        if 'Accelerated' in matchable_program.name_clean and 'Undergraduate' in matchable_program.program.career.name and 'Accelerated' in entry.type:
            threshold = 70

        return threshold
