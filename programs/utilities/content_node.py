from email.utils import parseaddr
from enum import Enum

from programs.models import College
from teledata.models import Building, Department

from bs4 import BeautifulSoup
import re

#region Helper Enums

class ContentNodeType(Enum):
    HEADING = 'heading'
    LIST = 'list'
    TABLE = 'table'
    CONTENT = 'content'

class ContentCategory(Enum):
    UNKNOWN = 'Unknown'
    GENERAL = 'General Info'
    ADMISSIONS = 'Admissions Info'
    COURSES = 'Course Info'
    CONTACT_INFO = 'Contact Info'
    DISPLAY = 'Display-related Content'

#endregion

college_names = [x.lower() for x in College.objects.values_list('full_name', flat=True)]
dept_names = [x.lower() for x in Department.objects.values_list('name', flat=True)]

class ContentNode(object):
    """
    Class used for analyzing a node of content
    from a degree description. This is usually
    and entire paragraph, a heading or a list.
    """
    #region Class Shared Variables

    PII_TYPES = [
        'NAME',
        'PERSON',
        'PHONE',
        'ADDRESS',
        'EMAIL',
        'ORGANIZATION'
    ]

    HEADING_TAGS = [
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6'
    ]

    #endregion

    #region Properties

    @property
    def node_type(self):
        """
        Gets the ContentNodeType of the ContentNode
        """
        if self.tag == None:
            return None

        if self.tag in self.HEADING_TAGS:
            return ContentNodeType.HEADING
        if self.tag in ['ul', 'ol', 'dl']:
            return ContentNodeType.LIST
        elif self.tag in ['table']:
            return ContentNodeType.TABLE
        else:
            return ContentNodeType.CONTENT

    #endregion

    #region Initializer

    def __init__(self, html_node, client=None):
        """
        Initializes the content node and runs the initial
        identification logic.
        """
        self.html_node = html_node

        # Let's make sure we have a comprehend client
        self.client = client
        if self.client == None:
            self.__initialize_client()

        self.content_category = ContentCategory.UNKNOWN
        self.__prepare()

    #endregion

    #region Private/Helper Functions

    def __prepare(self):
        """
        Entry point for the identification and classification
        logic. Sets up the variables needed for further processing.
        """
        self.tag = self.html_node.name

        # If a tag isn't set, we can't really work on this
        if self.tag is None:
            return

        self.cleaned_lines = self.__clean_html(str(self.html_node))
        self.cleaned_str = ' '.join(self.cleaned_lines)

        self.__set_node_details()

        # Set subheading, sibling elems (if this is a HEADING node)
        self.subheadings = self.__get_subheadings()
        self.next_sibling_headings = self.__get_next_sibling_headings()


    def __clean_html(self, html):
        """
        Grabs the text content within the HTML
        and preprares it for Comprehend processing.
        """
        soup = BeautifulSoup(html, 'html.parser')
        return [line for line in soup.stripped_strings]


    def __set_node_details(self):
        """
        Routing function. Based on what type of node we're
        dealing with, further type specific processing
        will happen.
        """
        if self.node_type == ContentNodeType.HEADING:
            self.__heading_processing()
        elif self.node_type == ContentNodeType.LIST:
            self.__list_processing()
        elif self.node_type == ContentNodeType.CONTENT:
            self.__content_processing()
        else:
            return

    def __heading_processing(self):
        """
        Processes nodes determined to be HEADINGs. We currently
        don't send these off to comprehend for processing and
        instead do simple string lookups.
        """
        cleaned_line = self.cleaned_str

        if any([x in cleaned_line.lower() for x in ['application', 'admission']]):
            self.content_category = ContentCategory.ADMISSIONS
        elif any([x in cleaned_line.lower() for x in ['curriculum', 'credit hour', 'electives']]):
            self.content_category = ContentCategory.COURSES
        elif any([x in cleaned_line.lower() for x in ['contact', 'address', 'phone']]):
            self.content_category = ContentCategory.CONTACT_INFO
        else:
            self.content_category = ContentCategory.UNKNOWN


    def __list_processing(self):
        """
        Processes nodes determined to be LISTs. We currently
        don't send these off to Comprehend for processing and
        instead do some regex lookups to determine if they
        contain program course information.
        """
        course_re = re.compile(r'([A-Za-z]{3,4}\s)([0-9]{4})([A-Za-z]{1})?')
        course_line_score = 0

        parsed_lines = []
        if self.node_type == ContentNodeType.LIST:
            # If this is actually a list already, extract text
            # from each child list item
            parsed_lines = [li.text for li in self.html_node.find_all(['li', 'dt', 'dd'], recursive=False)]
        else:
            # If this is something else (e.g. a paragraph),
            # just use self.cleaned_lines
            parsed_lines = self.cleaned_lines

        if parsed_lines:
            for li in parsed_lines:
                result = course_re.match(li)
                if result:
                    course_line_score += 100

            avg_score = course_line_score / len(parsed_lines)
        else:
            avg_score = 0

        if avg_score > 80:
            self.content_category = ContentCategory.COURSES
        else:
            self.content_category = ContentCategory.GENERAL

    def __content_processing(self):
        """
        Processes nodes determined to be CONTENT types. We
        split each separate line of content and send it off
        to AWS Comprehend for language processing.
        """
        cleaned_lines = self.cleaned_lines
        total_words = 0
        contact_info_score = 0

        # Handle single line nodes first, and convert them to
        # bulleted lists if they look like course listings:
        if len(cleaned_lines) == 1:
            self.__list_processing()

            if self.content_category == ContentCategory.COURSES:
                self.__convert_to_list()
                return

        # Determine if these lines of content look like contact info:
        for line in cleaned_lines:
            line_word_count = len(line.split(' '))
            total_words += line_word_count

            # Try to catch common types of contact info before passing
            # along to Comprehend:
            if self.__line_is_common_contact_info(line):
                contact_info_score += line_word_count * 100
            else:
                pii_response = self.__get_pii_entities(line)
                ent_response = self.__get_entities(line)

                if pii_response:
                    for pii_ent in pii_response['Entities']:
                        if pii_ent['Type'] in self.PII_TYPES:
                            b_offset = int(pii_ent['BeginOffset'])
                            e_offset = int(pii_ent['EndOffset'])
                            word_count = len(line[b_offset:e_offset].split(' '))
                            contact_info_score += pii_ent['Score'] * word_count * 100

                if ent_response:
                    for entity in ent_response['Entities']:
                        if entity['Type'] in self.PII_TYPES:
                            b_offset = int(entity['BeginOffset'])
                            e_offset = int(entity['EndOffset'])
                            word_count = len(line[b_offset:e_offset].split(' '))
                            contact_info_score += entity['Score'] * word_count * 100

        try:
            contact_info_avg = contact_info_score / total_words
        except ZeroDivisionError:
            contact_info_avg = 0

        # Finally, assign a content category:
        if contact_info_avg > 30:
            self.content_category = ContentCategory.CONTACT_INFO
        elif any([x in self.cleaned_str.lower() for x in ['scroll to', 'scroll down', 'scroll up']]):
            self.content_category = ContentCategory.DISPLAY
        elif any([x in self.cleaned_str.lower() for x in ['credit hour', 'course', 'elective']]):
            self.content_category = ContentCategory.COURSES
        elif any([x in self.cleaned_str.lower() for x in ['admission']]):
            self.content_category = ContentCategory.ADMISSIONS
        else:
            self.content_category = ContentCategory.GENERAL

    def __convert_to_list(self):
        """
        Takes a single paragraph line and converts it to a
        unordered list with a single list item.
        """
        inner_html = self.html_node.decode_contents().strip()
        new_content = "<ul><li>{0}</li></ul>".format(inner_html)
        new_soup = BeautifulSoup(new_content, 'html.parser')
        self.html_node = new_soup
        self.tag = 'ul'

    def __get_subheadings(self):
        """
        Returns immediate subheadings of the given node (non-recursive).
        Returns False if the given node is not the HEADING type.
        """
        if self.node_type != ContentNodeType.HEADING:
            return False

        if self.tag == 'h6':
            # can't have subheadings beyond this point
            return []

        # Increment through all possible immediate subheadings
        # for this node.
        # Accounts for skipped heading order (malformed markup.)
        subheadings = []
        possible_subheading_tags = self.HEADING_TAGS[self.HEADING_TAGS.index(self.tag) + 1:]

        for subheading_tag in possible_subheading_tags:
            if subheadings:
                break
            # Traverse the DOM for this type of subheading until
            # the next equivalent heading is found.
            # (e.g. if self.tag == 'h2', search for all adjacent h3s
            # until an adjacent h2 is found)
            for sibling in self.html_node.find_next_siblings([self.tag, subheading_tag]):
                if sibling.name == self.tag:
                    break
                elif sibling.name == subheading_tag:
                    subheadings.append(sibling)

        return subheadings

    def __get_next_sibling_headings(self):
        """
        Returns immediate sibling headings of the given node.
        Does not include previous siblings.
        Returns False if the given node is not the HEADING type.
        """
        if self.node_type != ContentNodeType.HEADING:
            return False

        siblings = []
        parent_tag = 'h{0}'.format(int(self.tag[1:2]) - 1)

        # Traverse the DOM for this type of sibling heading until
        # the next parent heading is found.
        # (e.g. if self.tag == 'h3', search for all adjacent h3s
        # until an adjacent h2 is found)
        for sibling in self.html_node.find_next_siblings([self.tag, parent_tag]):
            if sibling.name == parent_tag:
                break
            elif sibling.name == self.tag:
                siblings.append(sibling)

        return siblings

    def __line_is_common_contact_info(self, line):
        """
        Catches exact matches for common types of
        contact info that reside on their own lines of text.
        """
        retval = False

        # Is this line a phone/fax number?
        # NOTE: This check currently only tests against the basic phone
        # format 555-555-5555 (parentheses/spaces aren't accounted for)
        phone_re = re.compile(r'^((Telephone|Appointment Line|Fax)\: )?\d{3}\-\d{3}\-\d{4}$')
        phone_result = phone_re.fullmatch(line)

        # Is this line an email address?
        # https://stackoverflow.com/a/14485817
        email_parsed = parseaddr(line)
        email_result = '@' in email_parsed[1]

        # Is this line a common subhead-but-not-a-heading
        # (e.g. a single line wrapped in <strong>) for contact info?
        common_contact_subhead_result = line.lower() in [
            'mailing address',
            'institution codes',
            'graduate fellowships',
            'grad fellowships'
        ]

        # Does this line look like a college or
        # department name? (Useful as a fallback when
        # we can't make an exact string match)
        college_dept_re = re.compile(r'^(?:College of|Department of|Rosen College of) [a-zA-Z\ ]+$')
        college_dept_result = college_dept_re.match(line)

        if (
            phone_result
            or email_result
            or common_contact_subhead_result
            or (college_names and line.lower() in college_names)
            or (dept_names and line.lower() in dept_names)
            or college_dept_result
        ):
            retval = True

        return retval

    #endregion

    #region Comprehend Functions

    def __get_pii_entities(self, text):
        """
        Returns the PII (Personally Identifiable Information)
        results from AWS Comprehend for a bit of text.
        """
        response = None

        if text:
            response = self.client.detect_pii_entities(
                Text=text,
                LanguageCode='en'
            )

        return response

    def __get_entities(self, text):
        """
        Gets the general entities for a bit of text. This
        returns general results like names and organizations.
        """
        response = None

        if text:
            response = self.client.detect_entities(
                Text=text,
                LanguageCode='en'
            )

        return response

    #endregion

    #region Public Functions

    def increment_heading_tag(self, previous_heading_tag):
        """
        Increments or decrements a heading tag based on the
        `previous_heading` node passed in.
        """
        previous_idx = int(previous_heading_tag[1:2])

        # Don't increment past h6:
        if previous_idx < 6:
            self.change_tag('h{0}'.format(previous_idx + 1))

    def change_tag(self, new_tag):
        """
        Changes the name of the HTML tag for this node.
        """
        self.tag = new_tag
        self.html_node.name = new_tag

    #endregion
