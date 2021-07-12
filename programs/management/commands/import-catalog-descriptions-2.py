from django.core.management.base import BaseCommand
from django.conf import settings
from programs.utilities.oscar import Oscar

from programs.models import Program, ProgramDescription, ProgramDescriptionType, Level

from progress.bar import ChargingBar
import requests
import re
import unicodedata
import logging
import sys
from operator import itemgetter
from fuzzywuzzy import fuzz
import boto3
from bs4 import BeautifulSoup, NavigableString

from threading import Thread, Lock
from queue import Queue


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
    name = name.replace('Accel ', 'Accelerated ')

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
    name = ' '.join(
        [x for x in name.split() if x.lower() not in stop_words_ci])

    return name


class CatalogEntry(object):

    def __init__(self, json, program_type):
        self.data = json
        self.type = program_type
        self.match_count = 0
        self.program_description_clean = ''
        self.program_curriculum_clean = ''

    @property
    def level(self):
        """
        Translates a catalog entry's "program type" to an
        equivalent search service program's "Level".
        """
        try:
            temp_level = Level.objects.get(name=self.type)
            return temp_level
        except Level.DoesNotExist:
            pass

        if self.type in ['Major', 'Accelerated UndergraduateGraduate Program', 'Accelerated Undergraduate-Graduate Program', 'Articulated A.S. Programs']:
            return Level.objects.get(name='Bachelors')
        elif self.type == 'Certificate':
            return Level.objects.get(name='Certificate')
        elif self.type == 'Minor':
            return Level.objects.get(name='Minor')
        elif self.type in ['Master', 'Master of Fine Arts']:
            return Level.objects.get(name='Masters')

        return Level.objects.get(name='Bachelors')

    @property
    def name_clean(self):
        return clean_name(self.data['title'])

    @property
    def has_matches(self):
        return self.match_count > 0


class MatchableProgram(object):

    def __init__(self, program):
        self.program = program
        self.matches = [] # List of tuples containing score, CatalogEntry object
        self.best_match = None

    @property
    def name_clean(self):
        return clean_name(self.program.name)

    @property
    def has_matches(self):
        return len(self.matches) > 0

    def get_best_match(self):
        if self.has_matches:
            return max(self.matches, key=itemgetter(0))
        else:
            return None


class Command(BaseCommand):
    help = 'Imports catalog urls from the Kuali catalog system'

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            nargs='?',
            help='The base url of the Kuali API',
            default=settings.KUALI_BASE_URL
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='The api key used to connect to Kuali',
            dest='api-key',
            default=settings.KUALI_API_TOKEN,
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
            '--program-ids',
            type=int,
            nargs='*',
            help='''\
            One or more program IDs to import catalog data for. If set, only
            programs with the IDs provided will be processed/matched.
            ''',
            dest='program-ids',
            required=False
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            dest='skip_oscar',
            help='Skips calling Amazon Comprehend for full text analysis (do not feed Oscar)',
            default=False,
            required=False
        )
        parser.add_argument(
            '--threads',
            type=int,
            dest='max_threads',
            help='The number of concurrent threads to use',
            default=5,
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
        """
        The main entry point of the command

        Args:
            *args (list): A list of arguments from the command line.
            **options (dict): The dictionary list of keyword arguments
        """
        self.path = self.__trailingslashit(options['path'])
        self.key = options['api-key']
        self.catalog_url = self.__trailingslashit(options['catalog-url'])
        self.program_ids = options['program-ids']
        self.skip_oscar = options['skip_oscar']
        self.max_threads = options['max_threads']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Make sure these are actually set before continuing
        if not self.path or not self.key or not self.catalog_url:
            raise Exception(
                'Catalog URL base, API URL base and API key are required. Add these args to the import command or update settings_local.py.')

        self.matchable_programs = []
        self.catalog_url += 'catalog/{0}/#/programs/{1}'
        self.catalog_programs_url = f"{self.path}api/cm/programs/queryAll/"
        self.catalog_tracks_url = f"{self.path}api/cm/specializations/queryAll/"
        self.catalog_entries = []
        self.catalog_program_types = {}
        self.client = None
        if not self.skip_oscar:
            self.client = boto3.client(
                'comprehend',
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
                region_name=settings.AWS_REGION
            )

        # Let's setup some stats
        self.program_match_count = 0
        self.descriptions_updated_created = 0
        self.full_descriptions_updated_created = 0

        self.program_prep_progress = None
        self.catalog_prep_progress = None
        self.catalog_match_progress = None
        self.catalog_description_progress = None
        self.catalog_curriculum_progress = None
        self.program_update_progress = None

        # Setup our queues for multithreading
        self.catalog_description_queue = Queue()
        self.catalog_curriculum_queue = Queue()
        # General lock we can use when we need
        # to talk to the main thread
        self.mt_lock = Lock()

        # Get everything prepped/fetched
        self.__get_description_types()
        self.__get_programs()
        self.__get_catalog_entries()

        # Let's do some work
        self.__match_programs()
        self.__setup_description_processing()
        self.__setup_curriculum_processing()
        self.__update_programs()

        self.__print_stats()

    def __print_stats(self):
        """
        Prints the output of the command
        """
        p_to_c_match_percent = round(float(self.program_match_count) / float(len(self.matchable_programs) if len(self.matchable_programs) else 1) * 100, 2)
        c_with_match = len([x for x in self.catalog_entries if x.has_matches == True])
        c_to_m_match_percent = round(c_with_match / float(len(self.catalog_entries) if len(self.catalog_entries) else 1) * 100, 2)

        msg = f"""
Programs Processed        : {len(self.matchable_programs)}
Catalog Entries Processed : {len(self.catalog_entries)}

Matched {self.program_match_count}/{len(self.matchable_programs)} of Existing Programs to a Catalog Entry: {p_to_c_match_percent}%
Matched {c_with_match}/{len(self.catalog_entries)} of Fetched Catalog Entries to at Least One Existing Program: {c_to_m_match_percent}%

Short Descriptions Updated or Created : {self.descriptions_updated_created}
Full Descriptions Updated or Created  : {self.full_descriptions_updated_created}
        """

        self.stdout.write(self.style.SUCCESS(msg))

    def __trailingslashit(self, path):
        """
        Adds a trailing slash to a URL

        Args:
            path (str): The URL path

        Returns:
            (str) The URL with an appropriate ending slash
        """
        if path.endswith('/'):
            return path
        else:
            return f"{path}/"

    def __get_json_response(self, path, params={}, use_auth=True):
        """
        Requests content from a Kuali endpoint using a GET request
        and returns a serialized JSON object

        Args:
            path (str): The URL path to request
            params (dict): GET parameters to add to the request
            use_auth (bool): Whether the request requires the Authorization header

        Returns:
            (dict|array): The serialized JSON object as a dictionary (or array of dictionaries)
        """
        headers = {
            'content-type': 'application/json'
        }

        if use_auth:
            headers['Authorization'] = f'Bearer {self.key}'

        try:
            response = requests.get(
                path,
                params=params,
                headers=headers
            )

            data = response.json()

            return data

        except Exception as e:
            self.stderr.write(self.style.ERROR(str(e)))

    def __get_catalog_entries(self):
        """
        Requests programs/tracks from Kuali at the provided URL
        """
        catalog_program_data = self.__get_json_response(self.catalog_programs_url)
        catalog_tracks_data = self.__get_json_response(self.catalog_tracks_url)
        data = catalog_program_data['res'] + catalog_tracks_data['res']

        self.catalog_prep_progress = ChargingBar(
            'Prepping catalog entries...',
            max=len(data)
        )

        for result in data:
            self.catalog_prep_progress.next()

            # Catalog data must be active and have a title, academicLevel,
            # and programType field assigned to it for us to be able to
            # work with it. Additionally, we want to avoid nondegree programs:
            if 'status' in result and result['status'] == 'active' and 'title' in result and 'academicLevel' in result and ('programTypeUndergrad' in result or 'programTypeGrad' in result):
                catalog_program_type = self.__get_catalog_program_type(result)
                if catalog_program_type != 'Nondegree':
                    self.catalog_entries.append(
                        CatalogEntry(
                            result,
                            catalog_program_type
                        )
                    )

    def __get_catalog_program_type(self, catalog_entry_data):
        """
        Returns the string name of the program type of the
        provided catalog entry. (This maps to what we call the
        "level" in search service programs.)
        Args:
            catalog_entry_data (dict): The catalog entry JSON dictionary
        Returns:
            (str): The program type name string
        """
        program_type = None

        if 'programTypeUndergrad' in catalog_entry_data:
            try:
                program_type = self.catalog_program_types[catalog_entry_data['programTypeUndergrad']]
            except KeyError:
                program_type_data = self.__get_json_response(
                    f"{self.path}api/cm/options/{catalog_entry_data['programTypeUndergrad']}/")
                program_type = program_type_data['name']
                # Save it for reference later
                self.catalog_program_types[program_type_data['id']
                                           ] = program_type
        elif 'programTypeGrad' in catalog_entry_data:
            try:
                program_type = self.catalog_program_types[catalog_entry_data['programTypeGrad']]
            except KeyError:
                program_type_data = self.__get_json_response(
                    f"{self.path}api/cm/options/{catalog_entry_data['programTypeGrad']}/")
                program_type = program_type_data['name']
                # Save it for reference later
                self.catalog_program_types[program_type_data['id']
                                           ] = program_type

        return program_type

    def __get_description_types(self):
        """
        Ensures our description types are created
        """
        self.description_type, created = ProgramDescriptionType.objects.get_or_create(
            name='Catalog Description'
        )

        if created:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Catalog Description\" description type"
                )
            )

        self.description_type_full, created_full = ProgramDescriptionType.objects.get_or_create(
            name='Full Catalog Description'
        )

        if created_full:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Full Catalog Description\" description type"
                )
            )

    def __get_programs(self):
        """
        Grabs and preps existing programs to be matched with
        catalog entries.
        """
        programs = Program.objects.all()

        if self.program_ids:
            programs = programs.filter(pk__in=self.program_ids)

        self.program_prep_progress = ChargingBar(
            'Prepping existing programs...',
            max=len(programs)
        )

        for p in programs:
            self.program_prep_progress.next()

            # Wipe out existing catalog URL
            p.catalog_url = None
            p.save()

            # Wipe out existing catalog descriptions
            try:
                description = p.descriptions.get(
                    description_type=self.description_type)
                description.delete()
            except ProgramDescription.DoesNotExist:
                pass
            try:
                description_full = p.descriptions.get(
                    description_type=self.description_type_full)
                description_full.delete()
            except ProgramDescription.DoesNotExist:
                pass

            mp = MatchableProgram(p)
            self.matchable_programs.append(mp)

    def __match_programs(self):
        """
        Loops through the catalog entries and
        attempts to match them to existing programs.
        """
        self.catalog_match_progress = ChargingBar(
            'Matching existing programs to catalog entries...',
            max=len(self.matchable_programs)
        )

        for mp in self.matchable_programs:
            self.catalog_match_progress.next()

            # Create a list of CatalogEntry's to match against that
            # share the same career and level as the program:
            filtered_entries = [x for x in self.catalog_entries if x.level.name.lower(
            ) == mp.program.level.name.lower() and x.data['academicLevel'].lower() == mp.program.career.name.lower()]

            # Determine all potential catalog entry matches for the program:
            for entry in filtered_entries:
                match_score = fuzz.token_sort_ratio(
                    mp.name_clean, entry.name_clean)
                if match_score >= self.__get_match_threshold(mp, entry):
                    mp.matches.append((match_score, entry))

            if mp.has_matches:
                # Send the MatchableProgram off for further processing
                self.catalog_description_queue.put(mp)

                # Get the best match and save it for later
                match = mp.get_best_match()
                mp.best_match = matched_entry = match[1]

                # Increment match counts
                self.program_match_count += 1
                matched_entry.match_count += 1

                logging.log(
                    logging.INFO,
                    f"MATCH \n Matched program name: {mp.program.name} \n Cleaned program name: {mp.name_clean} \n Catalog entry full name: {matched_entry.data['title']} \n Cleaned catalog entry name: {matched_entry.name_clean} \n Match score: {match[0]} \n"
                )
            else:
                logging.log(
                    logging.INFO,
                    f"FAILURE \n Matched program name: {mp.program.name} \n Cleaned program name: {mp.name_clean} \n"
                )

    def __setup_description_processing(self):
        """
        Sets up multiple threads for processing
        catalog descriptions.
        """
        self.catalog_description_progress = ChargingBar(
            'Processing descriptions...',
            max=self.catalog_description_queue.qsize()
        )

        for _ in range(self.max_threads):
            Thread(target=self.__process_descriptions, daemon=True).start()

        self.catalog_description_queue.join()

    def __process_descriptions(self):
        while True:
            try:
                mp = self.catalog_description_queue.get()

                with self.mt_lock:
                    self.catalog_description_progress.next()

                catalog_entry = mp.best_match
                try:
                    catalog_desc = catalog_entry.data['programDescription']
                except:
                    catalog_desc = None

                if catalog_desc:
                    catalog_entry.program_description_clean = self.__sanitize_description(catalog_desc)

                # Pass along to the curriculum queue next
                self.catalog_curriculum_queue.put(mp)

            except Exception as e:
                logging.log(logging.ERROR, e)
            finally:
                self.catalog_description_queue.task_done()

    def __setup_curriculum_processing(self):
        """
        Sets up multiple threads for processing
        catalog curriculum data.
        """
        self.catalog_curriculum_progress = ChargingBar(
            'Processing curriculums...',
            max=self.catalog_curriculum_queue.qsize()
        )

        for _ in range(self.max_threads):
            Thread(target=self.__process_curriculums, daemon=True).start()

        self.catalog_curriculum_queue.join()

    def __process_curriculums(self):
        while True:
            try:
                mp = self.catalog_curriculum_queue.get()

                with self.mt_lock:
                    self.catalog_curriculum_progress.next()

                catalog_entry = mp.best_match
                try:
                    catalog_curriculum = catalog_entry.data['requiredCoreCourses']
                except:
                    catalog_curriculum = None

                if catalog_curriculum:
                    catalog_entry.program_curriculum_clean = self.__sanitize_description(catalog_curriculum, True)

            except Exception as e:
                logging.log(logging.ERROR, e)
            finally:
                self.catalog_curriculum_queue.task_done()

    def __update_programs(self):
        """
        Actually generates new ProgramDescription objects and
        updates catalog URLs on Program objects
        """
        self.program_update_progress = ChargingBar(
            'Updating programs...',
            max=len(self.matchable_programs)
        )

        for mp in self.matchable_programs:
            self.program_update_progress.next()

            catalog_entry = mp.best_match

            if catalog_entry:
                # Update the catalog URL of the program
                mp.program.catalog_url = self.catalog_url.format(
                    catalog_entry.data['academicLevel'],
                    catalog_entry.data['pid']
                )
                mp.program.save()

                # Create new program descriptions with the description
                # and curriculum info provided in the matched catalog entry
                description_str = self.__get_description(catalog_entry)
                if description_str:
                    description = ProgramDescription(
                        description_type=self.description_type,
                        description=description_str,
                        program=mp.program
                    )
                    description.save()
                    self.descriptions_updated_created += 1

                description_full_str = self.__get_full_description(catalog_entry)
                if description_full_str:
                    description_full = ProgramDescription(
                        description_type=self.description_type_full,
                        description=description_full_str,
                        program=mp.program
                    )
                    description_full.save()
                    self.full_descriptions_updated_created += 1

    def __get_description(self, catalog_entry):
        """
        Returns a shortened program description
        Args:
            catalog_entry (obj): a CatalogEntry object
        Returns:
            (str): The cleaned string
        """
        return catalog_entry.program_description_clean

    def __get_full_description(self, catalog_entry):
        """
        Returns a full catalog description
        Args:
            catalog_entry (obj): a CatalogEntry object
        Returns:
            (str): The cleaned string
        """
        return catalog_entry.program_description_clean + catalog_entry.program_curriculum_clean

    def __sanitize_description(self, description_str, strip_links=False):
        """
        Cleans the catalog entry string

        Args:
            catalog_entry (dict): The catalog entry JSON dictionary

        Returns:
            (str): The cleaned string
        """
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
        empty_tags = description_html.find_all(lambda tag: (not tag.contents or len(
            tag.get_text(strip=True)) <= 0) and not tag.name == 'br')
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
        p_tags = description_html.find_all(
            lambda tag: tag.name == 'p' and not tag.find(['ul', 'ol', 'dl', 'table']))
        for p_tag in p_tags:
            p_str = str(p_tag).replace('<p>', '').replace('</p>', '')
            substrings = re.split(r'(?:<br[\s]?[\/]?>[\s]*){2}', p_str)
            if len(substrings) > 1:
                substring_inserted = False
                for substring in substrings:
                    new_p = BeautifulSoup(
                        '<p>{0}</p>'.format(substring), 'html.parser')
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
        description_html = re.sub(
            r'^(Program|Track) Description<p>', '<p>', description_html)
        description_html = re.sub('1Active-Visible.*', '', description_html)
        description_html = re.sub(r'[\♦\►]', '', description_html)
        description_html = description_html.replace('<!--StartFragment-->', '')
        description_html = description_html.replace('<!--EndFragment-->', '')

        # Finally, pass along to Oscar:
        if not self.skip_oscar:
            oscar = Oscar(description_html, self.client)
            description_html = oscar.get_updated_description()

        return description_html

    def __get_match_threshold(self, matchable_program, entry):
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
