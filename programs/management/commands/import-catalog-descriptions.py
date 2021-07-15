from django.core.management.base import BaseCommand
from django.conf import settings
from programs.utilities.oscar import Oscar
from programs.utilities.catalog_match import CatalogEntry, MatchableProgram

from programs.models import Program, ProgramDescription, ProgramDescriptionType, Level

from progress.bar import ChargingBar
from datetime import datetime
import requests
import re
import unicodedata
import logging
import sys
import boto3
from bs4 import BeautifulSoup, NavigableString

from threading import Thread, Lock
from queue import Queue


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
            '--force-desc-updates',
            action='store_true',
            dest='force-desc-updates',
            help='If true, forces all catalog descriptions to be updated, regardless of whether or not they\'ve changed since the last import',
            default=False,
            required=False
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            dest='skip-oscar',
            help='Skips calling Amazon Comprehend for full text analysis (do not feed Oscar)',
            default=False,
            required=False
        )
        parser.add_argument(
            '--threads',
            type=int,
            dest='max-threads',
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
        self.start_time = datetime.now()
        self.path = self.__trailingslashit(options['path'])
        self.key = options['api-key']
        self.catalog_url = self.__trailingslashit(options['catalog-url'])
        self.program_ids = options['program-ids']
        self.force_desc_updates = options['force-desc-updates']
        self.skip_oscar = options['skip-oscar']
        self.max_threads = options['max-threads']
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
        self.catalog_colleges = {}
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
        self.catalog_match_queue = Queue()
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
        self.__setup_program_matching()
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

Finished in {datetime.now() - self.start_time}
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
        Requests programs/tracks from Kuali
        """
        catalog_program_data = self.__get_json_response(self.catalog_programs_url)
        catalog_tracks_data = self.__get_json_response(self.catalog_tracks_url)
        data = []

        try:
            data.extend(catalog_program_data['res'])
        except KeyError:
            pass
        try:
            data.extend(catalog_tracks_data['res'])
        except KeyError:
            pass

        self.catalog_prep_progress = ChargingBar(
            'Prepping catalog entries...',
            max=len(data)
        )

        for result in data:
            self.catalog_prep_progress.next()

            # Catalog data must be active and have a title, academicLevel,
            # and programType field assigned to it for us to be able to
            # work with it. Additionally, we want to avoid nondegree programs:
            if (
                'status' in result and result['status'] == 'active'
                and 'includeInCatalog' in result and result['includeInCatalog'] == True
                and 'title' in result
                and 'academicLevel' in result
                and ('programTypeUndergrad' in result or 'programTypeGrad' in result)
            ):
                catalog_program_type = self.__get_catalog_program_type(result)
                if catalog_program_type != 'Nondegree':
                    catalog_college_short = self.__get_catalog_college_short(result)
                    self.catalog_entries.append(
                        CatalogEntry(
                            result,
                            catalog_program_type,
                            catalog_college_short
                        )
                    )

    def __get_catalog_college_short(self, catalog_entry_data):
        """
        Returns a college's short name string for the
        provided catalog entry.

        Args:
            catalog_entry_data (dict): The catalog entry JSON dictionary

        Returns:
            (str): The catalog short name string
        """
        college_short = None

        if 'groupFilter1' in catalog_entry_data:
            college_id = catalog_entry_data['groupFilter1']

            try:
                college_short = self.catalog_colleges[college_id]
            except KeyError:
                try:
                    college_data = self.__get_json_response(
                        f"{self.path}api/v1/groups/{college_id}/"
                    )
                    # NOTE: not sure if I completely trust this ID
                    # to not change in the future...
                    college_short_data = next(
                        (item for item in college_data['fields']
                         if item['id'] == 'M2RCHsENP'),
                        None
                    )
                    if college_short_data:
                        college_short = college_short_data['value']
                except:
                    pass

            # Save it for reference later, even if it's None
            self.catalog_colleges[college_id] = college_short
        elif 'inheritedFrom' in catalog_entry_data:
            # This is a track; try to get the parent plan's college short name.
            # NOTE: assumes that top-level catalog programs were requested
            # first and have already been added to self.catalog_entries.
            parent_program_catalog_entry = next(
                (entry for entry in self.catalog_entries if entry.data['pid'] == catalog_entry_data['inheritedFrom']),
                None
            )
            if parent_program_catalog_entry:
                college_short = parent_program_catalog_entry.college_short

        return college_short

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
        program_type_id = None

        if 'programTypeUndergrad' in catalog_entry_data:
            program_type_id = catalog_entry_data['programTypeUndergrad']
        elif 'programTypeGrad' in catalog_entry_data:
            program_type_id = catalog_entry_data['programTypeGrad']

        if program_type_id:
            try:
                program_type = self.catalog_program_types[program_type_id]
            except KeyError:
                try:
                    program_type_data = self.__get_json_response(
                        f"{self.path}api/cm/options/{program_type_id}/"
                    )
                    program_type = program_type_data['name']
                except:
                    pass

            # Save it for reference later (even if it's None)
            self.catalog_program_types[program_type_id] = program_type

        return program_type

    def __get_description_types(self):
        """
        Ensures our description types are created
        """
        self.description_type_desc, created_desc = ProgramDescriptionType.objects.get_or_create(
            name='Catalog Description'
        )

        if created_desc:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Catalog Description\" description type"
                )
            )

        self.description_type_desc_full, created_desc_full = ProgramDescriptionType.objects.get_or_create(
            name='Full Catalog Description'
        )

        if created_desc_full:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Full Catalog Description\" description type"
                )
            )

        self.description_type_source_desc, created_source_desc = ProgramDescriptionType.objects.get_or_create(
            name='Source Catalog Description'
        )

        if created_source_desc:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Source Catalog Description\" description type"
                )
            )

        self.description_type_source_curriculum, created_source_curriculum = ProgramDescriptionType.objects.get_or_create(
            name='Source Catalog Curriculum'
        )

        if created_source_curriculum:
            self.stdout.write(
                self.style.NOTICE(
                    "Created \"Source Catalog Curriculum\" description type"
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

            mp = MatchableProgram(p)
            self.matchable_programs.append(mp)
            self.catalog_match_queue.put(mp)

    def __setup_program_matching(self):
        """
        Sets up multiple threads for matching catalog
        entries to existing programs.
        """
        self.catalog_match_progress = ChargingBar(
            'Matching existing programs to catalog entries...',
            max=self.catalog_match_queue.qsize()
        )

        for _ in range(self.max_threads):
            Thread(target=self.__match_programs, daemon=True).start()

        self.catalog_match_queue.join()

    def __match_programs(self):
        """
        Loops through the catalog entries and
        attempts to match them to existing programs.
        """
        while True:
            try:
                mp = self.catalog_match_queue.get()

                with self.mt_lock:
                    self.catalog_match_progress.next()

                # Create a list of CatalogEntry's to match against that
                # share the same career and level as the program, and
                # that share a college:
                filtered_entries = [
                    x for x in self.catalog_entries
                    if x.level == mp.program.level
                    and x.data['academicLevel'].lower() == mp.program.career.name.lower()
                    and (
                        x.college_short in mp.program.colleges.values_list('short_name', flat=True)
                        if x.college_short is not None
                        else True
                    )
                ]

                # Determine all potential catalog entry matches for the program:
                for entry in filtered_entries:
                    mp.match(entry)

                if mp.has_matches:
                    # Send the MatchableProgram off for further processing
                    self.catalog_description_queue.put(mp)

                    # Get the best match and save it for later
                    match = mp.get_best_match()
                    mp.best_match = match[1]

                    # Increment match counts
                    self.program_match_count += 1
                    mp.best_match.match_count += 1

                    logging.log(
                        logging.INFO,
                        f"MATCH \n Matched program name: {mp.program.name} \n Cleaned program name: {mp.name_clean} \n Catalog entry full name: {mp.best_match.data['title']} \n Cleaned catalog entry name: {mp.best_match.name_clean} \n Match score: {match[0]} \n"
                    )
                else:
                    logging.log(
                        logging.INFO,
                        f"FAILURE \n Matched program name: {mp.program.name} \n Cleaned program name: {mp.name_clean} \n"
                    )
            except Exception as e:
                logging.log(logging.ERROR, e)
            finally:
                self.catalog_match_queue.task_done()

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
        """
        Performs sanitization of catalog program descriptions.

        Will only perform sanitization when changes to existing
        descriptions are detected, or when the --force-desc-updates
        flag is True.
        """
        while True:
            try:
                mp = self.catalog_description_queue.get()

                with self.mt_lock:
                    self.catalog_description_progress.next()

                catalog_entry = mp.best_match
                catalog_desc = catalog_entry.description

                try:
                    source_desc_obj = mp.program.descriptions.get(
                        description_type=self.description_type_source_desc
                    )
                    source_desc = source_desc_obj.description if source_desc_obj.description else ''
                except ProgramDescription.DoesNotExist:
                    source_desc = ''

                if self.force_desc_updates or not source_desc or source_desc != catalog_desc:
                    # Sanitize/process the incoming catalog description if
                    # we don't already have an existing original catalog
                    # description to compare against, or if we do and it
                    # changed since the last time it was imported
                    # (or if we're forcing description updates)
                    if catalog_entry.program_description_clean is None:
                        catalog_entry.program_description_clean = self.__sanitize_description(
                            description_str=catalog_desc,
                            strip_tables=True
                        )

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
        """
        Performs sanitization of catalog curriculum content.

        Will only perform sanitization when changes to existing
        curriculums are detected, or when the --force-desc-updates
        flag is True.
        """
        while True:
            try:
                mp = self.catalog_curriculum_queue.get()

                with self.mt_lock:
                    self.catalog_curriculum_progress.next()

                catalog_entry = mp.best_match
                catalog_curriculum = catalog_entry.curriculum

                try:
                    source_curriculum_obj = mp.program.descriptions.get(
                        description_type=self.description_type_source_curriculum
                    )
                    source_curriculum = source_curriculum_obj.description if source_curriculum_obj.description else ''
                except ProgramDescription.DoesNotExist:
                    source_curriculum = ''

                if self.force_desc_updates or not source_curriculum or source_curriculum != catalog_curriculum:
                    # Sanitize/process the incoming catalog curriculum if
                    # we don't already have an existing original catalog
                    # curriculum to compare against, or if we do and it
                    # changed since the last time it was imported
                    # (or if we're forcing description updates)
                    if catalog_entry.program_curriculum_clean is None:
                        catalog_entry.program_curriculum_clean = self.__sanitize_description(
                            description_str=catalog_curriculum,
                            unwrap_links=True
                        )

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

            # Update the program with catalog data from
            # the best catalog entry match available:
            catalog_entry = mp.best_match

            if catalog_entry:
                # Update the catalog URL of the program
                mp.program.catalog_url = self.catalog_url.format(
                    catalog_entry.data['academicLevel'],
                    catalog_entry.data['pid']
                )
                mp.program.save()

                if catalog_entry.program_description_clean is not None or catalog_entry.program_curriculum_clean is not None:
                    # We processed a program description or curriculum
                    # for this catalog entry, so, remove all existing
                    # ProgramDescriptions related to the Program and
                    # create new ones:
                    self.__delete_program_descriptions(mp.program)

                    # Create new short and full program descriptions with the
                    # description and curriculum info provided in the matched
                    # catalog entry
                    description_str = self.__get_description(catalog_entry)
                    description = ProgramDescription(
                        description_type=self.description_type_desc,
                        description=description_str,
                        program=mp.program
                    )
                    description.save()
                    self.descriptions_updated_created += 1

                    description_full_str = self.__get_full_description(
                        catalog_entry
                    )
                    description_full = ProgramDescription(
                        description_type=self.description_type_desc_full,
                        description=description_full_str,
                        program=mp.program
                    )
                    description_full.save()
                    self.full_descriptions_updated_created += 1

                    # Create new ProgramDescriptions to store
                    # source program descriptions and curriculums
                    source_desc_str = catalog_entry.description
                    source_description = ProgramDescription(
                        description_type=self.description_type_source_desc,
                        description=source_desc_str,
                        program=mp.program
                    )
                    source_description.save()

                    source_curriculum_str = catalog_entry.curriculum
                    source_curriculum = ProgramDescription(
                        description_type=self.description_type_source_curriculum,
                        description=source_curriculum_str,
                        program=mp.program
                    )
                    source_curriculum.save()
                else:
                    # We did not process a program description or curriculum
                    # for this catalog entry, meaning we had existing,
                    # unchanged source data to reference.  Keep it intact.
                    pass
            else:
                # Remove any existing catalog URL on the program
                mp.program.catalog_url = None
                mp.program.save()

                # Delete any ProgramDescriptions assigned to the program
                self.__delete_program_descriptions(mp.program)

    def __get_description(self, catalog_entry):
        """
        Returns a shortened program description

        Args:
            catalog_entry (obj): a CatalogEntry object

        Returns:
            (str): The cleaned string
        """
        desc = ''

        if catalog_entry.program_description_clean is not None:
            desc = catalog_entry.program_description_clean

        return desc

    def __get_full_description(self, catalog_entry):
        """
        Returns a full catalog description

        Args:
            catalog_entry (obj): a CatalogEntry object

        Returns:
            (str): The cleaned string
        """
        desc = ''

        if catalog_entry.program_description_clean is not None:
            desc += catalog_entry.program_description_clean
        if catalog_entry.program_curriculum_clean is not None:
            desc += catalog_entry.program_curriculum_clean

        return desc

    def __delete_program_descriptions(self, program):
        """
        Deletes all ProgramDescriptions associated with the
        given Program

        Args:
            program (obj): Program object
        """
        # Delete any existing "short"/"full" catalog descriptions
        try:
            description_short = program.descriptions.get(
                description_type=self.description_type_desc)
            description_short.delete()
        except ProgramDescription.DoesNotExist:
            pass
        try:
            description_full = program.descriptions.get(
                description_type=self.description_type_desc_full)
            description_full.delete()
        except ProgramDescription.DoesNotExist:
            pass

        # Delete any existing original catalog descriptions
        # and curriculum content
        try:
            source_description = program.descriptions.get(
                description_type=self.description_type_source_desc)
            source_description.delete()
        except ProgramDescription.DoesNotExist:
            pass
        try:
            source_curriculum = program.descriptions.get(
                description_type=self.description_type_source_curriculum)
            source_curriculum.delete()
        except ProgramDescription.DoesNotExist:
            pass

    def __sanitize_description(self, description_str, unwrap_links=False, strip_tables=False):
        """
        Modifies the provided catalog description string
        to clean up markup and strip undesired tags/content.

        Args:
            description_str (str): The string to be processed
            strip_links (bool): Whether or not links should be removed from
                the final description markup

        Returns:
            (str): The cleaned string
        """
        if description_str == '':
            return description_str

        tag_whitelist = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'pre', 'sup', 'sub',
            'ul', 'li', 'ol', 'dl', 'dt', 'dd',
            'b', 'em', 'i', 'strong', 'u'
        ]
        if not unwrap_links:
            tag_whitelist.append('a')
        if not strip_tables:
            tag_whitelist.extend(['table', 'tbody', 'thead', 'tr', 'td'])

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

        # Strip tables, if enabled:
        if strip_tables:
            table_tags = description_html.find_all('table')
            for table_tag in table_tags:
                table_tag.decompose()

        for match in description_html.descendants:
            if isinstance(match, NavigableString) == False:
                # Transform <u> tags to <em>
                if match.name == 'u':
                    match.name = 'em'

                # Unwrap <p> tags within <li>s
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

                # Unwrap relative links, and links with no href
                if not unwrap_links and match.name == 'a':
                    href = match.get('href')
                    if not href or not href.startswith(('http', 'mailto', 'tel')):
                        match.name = 'span'
                        match.attrs = []

                # Unwrap inline tags in nested_tag_blacklist that
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
