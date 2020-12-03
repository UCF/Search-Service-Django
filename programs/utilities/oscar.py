import boto3
from bs4 import BeautifulSoup
import settings

from programs.utilities.content_node import ContentNode, ContentNodeType, ContentCategory
from io import StringIO

class Oscar:
    """
    Utility for transforming catalog descriptions.
    This will take description markup, as html, breaks
    down each top level "node" of content, identifies
    its type and category, and then removes the unwanted
    parts of the description.

    params
    ---------------

    description {string} The description to be transformed
    client {boto3.client} The AWS client used for comprehend API calls
    """

    #region Shared Class Variables

    SKIP = [
        ContentCategory.CONTACT_INFO
    ]

    #endregion

    #region Initializer

    def __init__(self, description, client=None):
        self.description = description

        self.client = client
        if self.client == None:
            self.__initialize_client()

        self.nodes = []

    #endregion

    #region Private Functions

    def __initialize_client(self):
        """
        Initializes the AWS client.
        """
        if (settings.AWS_ACCESS_KEY in [None, '']
            and settings.AWS_SECRET_KEY in [None, '']
            and settings.AWS_REGION == [None, '']):
            raise Exception('AWS_ACCESS_KEY, AWS_SECRET_KEY and AWS_REGION must be set in the settings_local.py file.')

        self.client = boto3.client(
            'comprehend',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )

    def __remove_empty(self):
        """
        Removes nodes that have no content
        """
        setval = []

        for node in self.nodes:
            if str(node.html_node).strip() != '':
                setval.append(node)

        self.nodes = setval

    def __organize_nodes(self):
        """
        Makes various decisions about removing or updating
        nodes based on the logic below.
        """
        setval = []

        previous_node = None
        previous_headings = {
            'h2': None,
            'h3': None,
            'h4': None,
            'h5': None
        }

        for idx, node in enumerate(nodes):
            # If this node is in a category that should be skipped
            if node.content_category in skip:
                continue

            # If this node is a title, and there's more
            # content after it, and that content is skippable,
            # then skip this title. We don't want it.
            if (node.node_type == ContentNodeType.TITLE
                and len(self.nodes) > idx + 1
                and self.nodes[idx + 1].content_category in self.SKIP):
                continue

            # If the previous and next node are skippable,
            # then skip this one too.
            if (previous_node
                and len(nodes) > idx + 1
                and previous_node.content_category in skip
                and nodes[idx + 1].content_category in skip):
                continue

            # If this is a title, make sure headings are ordered correctly:
            if node.node_type == ContentNodeType.TITLE:
                # Don't allow h1's:
                if node.tag == 'h1':
                    node.change_tag('h2')
                # Enforce correct ordering of immediate subheadings:
                else:
                    for prev_heading_tag, prev_heading_node in previous_headings.items():
                        if prev_heading_node and node.html_node in prev_heading_node.subheadings:
                            node.increment_title_tag(prev_heading_node)

                previous_headings[node.tag] = node

            # By default, just add the node
            setval.append(node)
            previous_node = node

        self.nodes = setval


    #endregion

    #region Public functions

    def get_updated_description(self):
        buffer = StringIO()
        soup = BeautifulSoup(self.description, 'html.parser')

        for node in soup.contents:
            content_node = ContentNode(node, self.client)
            self.nodes.append(content_node)

        self.__remove_empty()
        self.__organize_nodes()

        for node in self.nodes:
            buffer.write(str(node.html_node))

        retval = buffer.getvalue()
        buffer.close()
        return retval

    #endregion
