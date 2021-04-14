from django.core.management.base import BaseCommand, CommandError
from programs.models import *
from programs.utilities.oscar import Oscar

import requests
import re
import boto3
import itertools
import logging
import sys
from operator import attrgetter
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup, NavigableString
import unicodedata


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

    def __init__(self, id, name, program_type, catalog_id):
        self.id = id
        self.name = name.decode()
        self.type = program_type.decode()
        self.catalog_id = catalog_id
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
            nargs='?',
            help='The base url of the Acalog API',
            default=settings.CATALOG_API_BASE
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='The api key used to connect to Acalog',
            dest='api-key',
            default=settings.CATALOG_API_KEY,
            required=False
        )
        parser.add_argument(
            '--catalog-id',
            type=int,
            help='The ID of the catalog to use',
            dest='catalog-id',
            required=False
        )
        parser.add_argument(
            '--catalog-url',
            type=str,
            help='The url to use when building catalog urls',
            dest='catalog-url',
            default=settings.CATALOG_URL_BASE,
            required=False
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
            '--program-ids',
            type=int,
            nargs='*',
            help='''\
            One or more program IDs to import catalog data for. Supersedes the
            `--catalog-id` arg if provided, and depends on undergraduate and
            graduate catalog IDs set in settings_local.
            ''',
            dest='program-ids',
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
        self.catalog_url = options['catalog-url']

        # Make sure these are actually set before continuing
        if not self.path or not self.key or not self.catalog_url:
            raise Exception('Catalog URL base, API URL base and API key are required. Add these args to the import command or update settings_local.py.')

        self.catalog_url += '/preview_program.php?catoid={0}&poid={1}'

        self.program_ids = options['program-ids']
        self.graduate = options['graduate']
        self.catalog_id = options['catalog-id']
        if self.catalog_id is None and not self.program_ids:
            self.catalog_id = settings.CATALOG_GRADUATE_ID if self.graduate else settings.CATALOG_UNDERGRADUATE_ID

        self.loglevel = options['loglevel']
        self.client = boto3.client(
            'comprehend',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Retrieve catalog data
        if self.program_ids:
            careers = Career.objects.filter(program__pk__in=self.program_ids).distinct()

            for career in careers:
                if career.name == 'Undergraduate':
                    catalog_id = settings.CATALOG_UNDERGRADUATE_ID
                elif career.name == 'Graduate':
                    catalog_id = settings.CATALOG_GRADUATE_ID

                program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(self.path, self.key, catalog_id)

                self.get_catalog_programs(program_url, catalog_id)
        else:
            program_url = '{0}search/programs?key={1}&format=xml&method=listing&catalog={2}&options%5Blimit%5D=500'.format(self.path, self.key, self.catalog_id)

            self.get_catalog_programs(program_url, self.catalog_id)

        # Start matching up programs by name
        self.match_programs()

        return 0

    def get_catalog_programs(self, program_url, catalog_id):
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
                        result.find('type').text.encode('ascii', 'ignore'),
                        catalog_id
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

        if self.program_ids:
            programs = programs.filter(pk__in=self.program_ids)
        else:
            if self.graduate:
                career_name = 'Graduate'
            else:
                career_name = 'Undergraduate'

            programs = programs.filter(career__name=career_name)

        for p in programs:
            # Is this a graduate program?
            # (Necessary when running import by program IDs)
            if self.program_ids:
                is_graduate = p.career.name == 'Graduate'
            else:
                is_graduate = self.graduate

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
                p.program.catalog_url = self.catalog_url.format(matched_entry.catalog_id, matched_entry.id)
                p.program.save()

                # Create new program descriptions with the description provided in the matched catalog entry
                description_str = self.get_description(
                    matched_entry.id,
                    matched_entry.catalog_id,
                    is_graduate
                )
                if description_str:
                    description = ProgramDescription(
                        description_type=description_type,
                        description=description_str,
                        program=p.program
                    )
                    description.save()

                description_full_str = self.get_description_full(
                    matched_entry.id,
                    p.program.catalog_url
                )
                if description_full_str:
                    description_full = ProgramDescription(
                        description_type=description_type_full,
                        description=description_full_str,
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


    def get_description(self, program_id, catalog_id, is_graduate):
        url = '{0}content?key={1}&format=xml&method=getItems&type=programs&ids[]={2}&catalog={3}'.format(
            self.path,
            self.key,
            program_id,
            catalog_id
        )

        try:
            response = requests.get(url)
            encoding = response.encoding
            raw_data = response.text.encode(encoding)
        except Exception as e:
            logging.error('Error requesting catalog description: {0}'.format(e))
            return ''

        # Strip xmlns attributes to parse string to xml without namespaces
        data = re.sub(b' xmlns(?:\:[a-z]*)?="[^"]+"', b'', raw_data)
        root = BeautifulSoup(data, 'xml')

        try:
            if is_graduate:
                cores = root.find('cores')
                description_xml = cores.find('core').find('content').encode_contents()
            else:
                description_xml = root.find('content').encode_contents()
        except Exception as e:
            logging.error('Error parsing catalog description XML: {0}'.format(e))
            return ''

        # Sanitize contents:
        description_html = self.sanitize_description(description_xml)

        return description_html

    def get_description_full(self, program_id, catalog_url):
        try:
            response = requests.get(catalog_url, verify=False)  # :(
            encoding = response.encoding
            raw_data = response.text.encode(encoding)
        except Exception as e:
            logging.error('Error requesting catalog description: {0}'.format(e))
            return ''

        root = BeautifulSoup(raw_data, 'html.parser')

        description_str = ''
        desc_parts = root.select('.block_content > .table_default > tr')

        try:
            desc_1_row = desc_parts[0]
        except IndexError:
            desc_1_row = None

        try:
            desc_2_row = desc_parts[1]
        except IndexError:
            desc_2_row = None

        # Parse first part of description, which is basically
        # everything up to course listings/plans of study.
        # Ignore table nodes in this row (assume they're just
        # contact info):
        if desc_1_row:
            for desc_1_node in desc_1_row.find(class_='table_default').next_siblings:
                if isinstance(desc_1_node, NavigableString) == False and desc_1_node.name != 'table':
                    description_str += str(desc_1_node)

        # Parse second description part:
        if desc_2_row and hasattr(desc_2_row, 'td'):
            for desc_2_node in desc_2_row.td:
                if isinstance(desc_2_node, NavigableString) == False:
                    description_str += str(desc_2_node)

        # Back out now if no description contents were found:
        if not description_str:
            return ''

        # Sanitize contents:
        description_html = self.sanitize_description(description_str, strip_links=True)

        return description_html

    def sanitize_description(self, description_str, strip_links=False):
        """
        Modifies the provided catalog description string
        to clean up markup and strip undesired tags/content.
        """
        tag_whitelist = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'pre', 'sup', 'sub',
            'table', 'tbody', 'thead', 'tr', 'td',
            'ul', 'li', 'ol', 'dl', 'dt', 'dd',
            'b', 'em', 'i', 'strong', 'u'
        ]
        if not strip_links:
            tag_whitelist.append('a')

        # Tags that should not allow nesting of the same
        # tag type (e.g. <em><em>...</em></em>),
        # nor surround all inner heading contents
        # (e.g. <h2><strong>...</strong></h2>)
        nested_tag_blacklist = ['b', 'em', 'i', 'strong']

        attr_blacklist = [
            'class', 'style',
            'border', 'cellpadding', 'cellspacing'
        ]

        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # Make some soup:
        description_html = BeautifulSoup(description_str, 'html.parser')

        # Strip empty tags:
        empty_tags = description_html.find_all(lambda tag: (not tag.contents or len(tag.get_text(strip=True)) <= 0) and not tag.name == 'br')
        for empty_tag in empty_tags:
            empty_tag.decompose()

        for match in description_html.descendants:
            if isinstance(match, NavigableString) == False:
                # Transform <u> tags to <em>
                if match.name == 'u':
                    match.name = 'em'

                # Strip <p> tags within <li>s
                if match.name == 'p' and match.parent.name == 'li':
                    match.name = 'span'
                    match.attrs = []

                # Remove nested tags of the same type within the tag,
                # if it's in the nested_tag_blacklist
                if match.name in nested_tag_blacklist:
                    nested_tags = match.find_all(match.name)
                    for nested_tag in nested_tags:
                        nested_tag.name = 'span'
                        nested_tag.attrs = []

                # Remove relative links, and links with no href
                if not strip_links and match.name == 'a':
                    href = match.get('href')
                    if not href or not href.startswith(('http', 'mailto', 'tel')):
                        match.name = 'span'
                        match.attrs = []

                # Remove inline tags in nested_tag_blacklist that
                # surround all content within headings
                if match.name in heading_tags:
                    inner_tag = match.find(nested_tag_blacklist)
                    if (
                        inner_tag
                        and inner_tag.string
                        and match.string
                        and inner_tag.string.strip() == match.string.strip()
                    ):
                        inner_tag.name = 'span'
                        inner_tag.attrs = []

                if match.name not in tag_whitelist:
                    # Filter out tags not in our whitelist (replace them with span's)
                    match.name = 'span'
                    match.attrs = []
                else:
                    # Remove unused attrs from elements
                    for bad_attr in attr_blacklist:
                        if bad_attr in match.attrs:
                            match.attrs.pop(bad_attr)

        # BS seems to have a hard time with doing this in-place, so perform
        # a second loop to remove the garbage tags
        for span_match in description_html.find_all('span'):
            span_match.unwrap()

        # Split paragraph tag contents by subsequent <br> tags (<br><br>)
        # and transform each split chunk into its own new paragraph.
        # NOTE: These p tags _shouldn't_ have nested elements like
        # these, but just in case, make sure we ignore them:
        p_tags = description_html.find_all(lambda tag: tag.name == 'p' and not tag.find(['ul', 'ol', 'dl', 'table']))
        for p_tag in p_tags:
            p_str = str(p_tag).replace('<p>', '').replace('</p>', '')
            substrings = re.split(r'(?:<br[\s]?[\/]?>[\s]*){2}', p_str)
            if len(substrings) > 1:
                substring_inserted = False
                for substring in substrings:
                    new_p = BeautifulSoup('<p>{0}</p>'.format(substring), 'html.parser')
                    new_p = new_p.find('p')
                    # Make sure new paragraphs aren't empty:
                    if len(new_p.get_text(strip=True)) > 0:
                        p_tag.insert_before(new_p)
                        substring_inserted = True
                if substring_inserted:
                    p_tag.decompose()

        # Un-soup(?) the soup
        description_html = str(description_html)

        # Strip newlines:
        description_html = re.sub(r'[\r\n\t]', ' ', description_html)

        # Fix various garbage characters
        description_html = unicodedata.normalize('NFKC', description_html)
        description_html = description_html.replace('\u200b', '')

        # Some of these descriptions have likely been through some sort
        # of back-and-forth between encodings via copy+paste, and contain
        # stray diacritics (e.g. "Â") not caught via filtering logic above.
        # They were likely non-breaking space characters in a past life.
        # https://stackoverflow.com/a/1462039
        # Just get rid of them here:
        description_html = description_html.replace('Â', '')

        # Other miscellaneous string replacements:
        description_html = re.sub(r'^(Program|Track) Description<p>', '<p>', description_html)
        description_html = re.sub('1Active-Visible.*', '', description_html)
        description_html = re.sub(r'[\♦\►]', '', description_html)
        description_html = description_html.replace('<!--StartFragment-->', '')
        description_html = description_html.replace('<!--EndFragment-->', '')

        # Finally, pass along to Oscar:
        oscar = Oscar(description_html, self.client)
        description_html = oscar.get_updated_description()

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
