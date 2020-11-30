from enum import Enum

from bs4 import BeautifulSoup
import re

#region Helper Enums

class ContentNodeType(Enum):
    TITLE = 'title'
    LIST = 'list'
    LIST_ITEM = 'list item'
    TABLE = 'table'
    CONTENT = 'content'

class ContentCategory(Enum):
    UNKNOWN = 'Unknown'
    GENERAL = 'General Info'
    ADMISSIONS = 'Admissions Info'
    COURSES = 'Course Info'
    CONTACT_INFO = 'Contact Info'

#endregion

class ContentNode(object):
    """
    Class used for analyzing a node of content
    from a degree description. This is usually
    and entire paragraph, a heading or a list.
    """
    #region Class Shared Variables

    PII_TYPES = [
        'NAME',
        'PHONE',
        'ADDRESS',
        'EMAIL',
        'ORGANIZATION'
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

        if self.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return ContentNodeType.TITLE
        if self.tag in ['ul', 'ol', 'dl']:
            return ContentNodeType.LIST
        elif self.tag in ['li']:
            return ContentNodeType.LIST_ITEM
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

        self.lines = []

        self.cleaned = self.__clean_html(str(self.html_node))

        self.__set_node_details()


    def __clean_html(self, html):
        """
        Grabs the text content within the HTML
        and preprares it for Comprehend processing.
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n').strip()


    def __set_node_details(self):
        """
        Routing function. Based on what type of node we're
        dealing with, further type specific processing
        will happen.
        """
        if self.node_type == ContentNodeType.TITLE:
            self.__title_processing()
        elif self.node_type == ContentNodeType.LIST:
            self.__list_processing()
        elif self.node_type == ContentNodeType.LIST_ITEM:
            self.__list_item_processing()
        elif self.node_type == ContentNodeType.CONTENT:
            self.__content_processing()
        else:
            return

    def __title_processing(self):
        """
        Processes nodes determined to be TITLEs. We currently
        don't send these off to comprehend for processing and
        instead do simple string lookups.
        """
        cleaned_line = self.cleaned.strip()
        self.lines.append({
            'text': cleaned_line,
            'personal_data': [],
            'entities': []
        })

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
        don't send these off to comprehend for processing and
        instead do some regex lookups to determine if they
        contain progam course information.
        """
        course_re = re.compile(r'([A-Za-z]{3,4}\s)([0-9]{4})')

        cleaned_lines = self.cleaned.splitlines()
        course_line_score = 0

        for line in cleaned_lines:
            result = course_re.match(line)
            if result:
                course_line_score += 100

        avg_score = course_line_score / len(cleaned_lines)

        if avg_score > 80:
            self.content_category = ContentCategory.COURSES
        else:
            self.content_category = ContentCategory.GENERAL

    def __list_item_processing(self):
        """
        Not used. TODO: Consider removing.
        """
        pass

    def __content_processing(self):
        """
        Processes nodes determined to be CONTENT types. We
        split each separate line of content and send it off
        to AWS Comprehend for language processing.
        """
        cleaned_lines = self.cleaned.splitlines()

        contact_info_score = 0
        contact_re = re.compile(r'^(?:College of|Department of|Rosen College of) [a-zA-Z\ ]+$')

        if len(cleaned_lines) == 1:
            self.__list_processing()

            if self.content_category == ContentCategory.COURSES:
                self.__convert_to_list()
                return

        for line in cleaned_lines:
            line = line.strip()
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

            # Addition processing to catch contact info
            result = contact_re.match(line)

            if result:
                contact_info_score += len(line.split(' ')) * 100

        total_words = len(self.cleaned.split(' '))
        contact_info_avg = contact_info_score / total_words

        if contact_info_avg > 30:
            self.content_category = ContentCategory.CONTACT_INFO
        elif any([x in self.cleaned.lower() for x in ['credit hour', 'course', 'elective']]):
            self.content_category = ContentCategory.COURSES
        elif any([x in self.cleaned.lower() for x in ['admission']]):
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

    def increment_title_tag(self, previous_heading):
        """
        Increments or decrements a heading based on the
        `previous_heading` node passed in.
        """
        previous_idx = int(previous_heading.tag[1:2])
        self.tag = 'h{0}'.format(previous_idx + 1)

    #endregion
