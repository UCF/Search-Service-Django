from operator import itemgetter
from fuzzywuzzy import fuzz
from datetime import datetime

from programs.models import Level, Career, Program


class CatalogEntry(object):
    """
    Describes a catalog program or track and
    its associated data.
    """
    def __init__(self, json, html_data, program_type, college_short):
        self.data = json
        self.html_data = html_data
        self.type = program_type
        self.college_short = college_short
        self.match_count = 0
        self.program_description_clean = None
        self.program_curriculum_clean = None
        self.level_pk = self.level.pk
        self.career_pk = self.career.pk

        self.plan_code = None
        self.subplan_code = None
        self.parent_catalog_id = None

        # Set plan code or subplan code
        if 'inheritedFrom' not in self.data and 'code' in self.data:
            self.plan_code = self.data['code']
        else:
            self.parent_catalog_id = self.data['inheritedFrom']
            self.subplan_code = self.data['code']


    @property
    def description(self):
        """
        Returns an unmodified catalog program description

        Returns:
            (str): Catalog description string
        """
        desc = ''

        # Short description
        if 'programDescription' in self.data:
            # Catalog programs:
            desc += self.data['programDescription']
        elif 'description' in self.data:
            # Catalog tracks:
            desc += self.data['description']

        # Licensure Disclosure
        if 'licensureDisclosureNotes' in self.data and 'licensureDisclosure' in self.data and self.data['licensureDisclosure'] == True:
            desc += self.data['licensureDisclosureNotes']

        # UCF Online blurb
        if 'ucfOnlineContent' in self.data and 'fullyOnline' in self.data and self.data['fullyOnline'] == 'yes':
            # Catalog programs:
            desc += self.data['ucfOnlineContent']
        elif 'ucfOnlineContentTrack' in self.data and 'onlineAvailability' in self.data and self.data['onlineAvailability'] == 'yes':
            # Catalog tracks:
            desc += self.data['ucfOnlineContentTrack']

        return desc

    @property
    def curriculum(self):
        """
        Returns an original catalog curriculum string

        Returns:
            (str): Catalog curriculum string
        """
        curriculum = ''

        # Assume dedicated fields for extended curriculum-related
        # data are in use if `degreeRequirements` is present in
        # self.html_data and is not empty:
        if 'degreeRequirements' in self.html_data and self.html_data['degreeRequirements'] != '':
            # NOTE: Headings starting at h1 are intentional here.
            # Headings in fields in `data_html` tend to start at h2,
            # so by using h1s here, we allow Oscar to determine
            # proper heading order and fix things later:

            # For undergrad programs, pull in the prerequisite admission field
            if self.career.name == 'Undergraduate' \
                and 'prerequisiteAdmissionUg' in self.html_data and \
                isinstance(self.html_data['prerequisiteAdmissionUg'], str):
                curriculum += f"<h1>Program Prerequisites</h1>{self.html_data['prerequisiteAdmissionUg']}"


            # Prerequisites
            if 'programPrerequisites' in self.data:
                # Catalog programs:
                curriculum += f"<h1>Program Prerequisites</h1>{self.data['programPrerequisites']}"
            elif 'trackPrerequisites' in self.data:
                # Catalog tracks:
                curriculum += f"<h1>Track Prerequisites</h1>{self.data['trackPrerequisites']}"

            # Degree requirements (course listings)
            # NOTE: must check for "course not found" here; Kuali can
            # cache bad content like this, which we don't want to inherit
            if 'course not found' not in self.html_data['degreeRequirements'].lower():
                curriculum += f"<h1>Degree Requirements</h1>{self.html_data['degreeRequirements']}"

            # Application requirements
            if 'applicationRequirements' in self.data:
                curriculum += f"<h1>Application Requirements</h1>{self.data['applicationRequirements']}"

            # Application deadlines
            if 'applicationDeadlineText' in self.data:
                curriculum += f"<h1>Application Deadlines</h1>{self.data['applicationDeadlineText']}"

                if 'applicationDeadlinesNotes' in self.data:
                    # Catalog programs:
                    curriculum += self.data['applicationDeadlinesNotes']
                elif 'applicationNotesTrack' in self.data:
                    # Catalog tracks:
                    curriculum += self.data['applicationNotesTrack']

            # Financial info
            if 'financialInformation' in self.data:
                curriculum += f"<h1>Financial Information</h1>{self.data['financialInformation']}"

            # Fellowship info
            if 'fellowshipInformation' in self.data:
                curriculum += f"<h1>Fellowship Information</h1>{self.data['fellowshipInformation']}"

            # Let's go ahead and pull in requiredCoreCourses at the very
            # beginning of descriptions.
            if 'requiredCoreCourses' in self.data:
                curriculum += self.data['requiredCoreCourses']
        elif 'requiredCoreCourses' in self.data:
            curriculum = self.data['requiredCoreCourses']

        return curriculum

    @property
    def level(self):
        """
        Translates a catalog entry's "program type" to an
        equivalent search service program's "Level".

        Returns:
            (object): Level object
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
    def career(self):
        """
        Translates a catalog entry's "academic level" to an
        equivalent search service program's "Career".

        Returns:
            (object): Career object
        """
        career = None

        try:
            career = Career.objects.get(
                name__iexact=self.data['academicLevel']
            )
        except Career.DoesNotExist:
            career = Career.objects.get(name='Undergraduate')

        return career

    @property
    def name_clean(self):
        """
        Returns the title of the program/track,
        suitable for string matching.

        Returns:
            (str): The cleaned program/track title
        """
        return clean_name(self.data['title'])

    @property
    def has_matches(self):
        """
        Returns whether or not the CatalogEntry
        has at least one match to a MatchableProgram.

        Returns:
            (bool): Whether or not at least one
                MatchableProgram match exists
        """
        return self.match_count > 0


    @property
    def required_core_courses(self):
        if 'requiredCoreCourses' in self.data and self.data['requiredCoreCourses'] is not None:
            return self.data['requiredCoreCourses']
        else:
            return ""

class MatchableProgram(object):
    """
    Describes a Program and its match(es) to CatalogEntries.
    """
    def __init__(self, program: Program):
        self.program = program
        self.matches = []  # List of tuples containing score, CatalogEntry object
        self.best_match = None
        self.level_pk = self.program.level.pk
        self.career_pk = self.program.career.pk

    @property
    def name_clean(self):
        """
        Returns the Program object's name, suitable for
        string matching.

        Returns:
            (str): The cleaned Program name
        """
        return clean_name(self.program.name)

    @property
    def has_matches(self):
        """
        Returns whether or not the MatchableProgram
        has at least one match to a CatalogEntry.

        Returns:
            (bool): Whether or not at least one
                CatalogEntry match exists
        """
        return len(self.matches) > 0

    def match(self, catalog_entry):
        """
        Determines whether or not the provided catalog_entry can be
        matched with this MatchableProgram by program name, and stores
        the match and its match score if it does.
        """
        match_score = self.__get_code_match(
            catalog_entry
        )

        if match_score != 100:
            match_score = fuzz.token_sort_ratio(
                self.name_clean,
                catalog_entry.name_clean
            )

        if match_score >= self.__get_match_threshold(catalog_entry):
            self.matches.append((match_score, catalog_entry))


    def __get_code_match(self, catalog_entry):
        """
        Tries to match the "code" field with the
        plan_code of the program.
        """
        # If this is a parent program
        if self.program.parent_program == None:
            if self.program.plan_code == catalog_entry.plan_code:
                return 100
        else: # If this is a subplan
            if self.program.plan_code == catalog_entry.plan_code and \
                self.program.subplan_code == catalog_entry.subplan_code:
                return 100

        return 0


    def get_best_match(self):
        """
        Returns the match in self.matches with the highest match score.

        Returns:
            (object|None): Highest-scoring CatalogEntry match, or None
        """
        if self.has_matches:
            max_match = max(self.matches, key=itemgetter(0))
            code = max_match[1].data['code']
            similar_matches = [
                x for x in self.matches
                    if x[1].data['code'] == code
                    and 'dateStart' in x[1].data
                    and datetime.strptime(x[1].data['dateStart'], '%Y-%m-%d') < datetime.now()
            ]
            return max(
                similar_matches,
                key=lambda x: datetime.strptime(x[1].data['dateStart'], '%Y-%m-%d')
            ) if len(similar_matches) > 0 else max_match
        else:
            return None

    def __get_match_threshold(self, catalog_entry):
        """
        Determines the minimum match score the provided catalog_entry
        must have in order to be a match with this MatchableProgram.

        Args:
            catalog_entry (object): a CatalogEntry to determine a mimimum match score for

        Returns:
            (int): The minimum match score for the CatalogEntry to be a match
        """
        # Base threshold score value. Increase base threshold
        # for graduate programs.
        threshold = 80
        if self.program.career.name == 'Graduate':
            threshold = 85

        # Determine the mean (average) number of words between the
        # existing program name and catalog entry name
        word_count_mp = len(self.name_clean.split())
        word_count_e = len(catalog_entry.name_clean.split())
        word_counts = [word_count_mp, word_count_e]
        try:
            word_count_mean = float(sum(word_counts)) / max(len(word_counts), 1)
        except ZeroDivisionError:
            pass

        # Enforce a stricter threshold between program names with a lower
        # mean word count
        if word_count_mean <= 3:
            threshold += 2

        if word_count_mean <= 2:
            threshold += 3

        # Enforce stricter threshold for subplans, since they have a decent
        # chance of unintentionally matching against their parent program when
        # they shouldn't
        if self.program.is_subplan:
            threshold = 90

        # Reduce the threshold for accelerated undergraduate programs, since
        # their names tend to vary more greatly between the catalog and
        # our data
        if 'Accelerated' in self.name_clean and 'Undergraduate' in self.program.career.name and 'Accelerated' in catalog_entry.type:
            threshold = 70

        return threshold


def clean_name(program_name):
    """
    Helper function that sanitizes and normalizes a
    program name for string matching purposes.

    Args:
        program_name (str): The name of a program

    Returns:
        (str): The sanitized program name
    """
    name = program_name

    name = program_name.replace(' Undergraduate', '').replace(' Graduate', '')

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
