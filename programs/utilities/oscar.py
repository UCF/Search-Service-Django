import boto3
from bs4 import BeautifulSoup
import settings

from programs.utilities.content_node import ContentNode, ContentNodeType, ContentCategory
from io import StringIO

class Oscar:

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
        previous_heading = None

        for idx, node in enumerate(self.nodes):
            # If this node is a title, and there's more
            # content after it, and that content is skippable,
            # then skip this title. We don't want it.
            if (node.node_type == ContentNodeType.TITLE
                and len(self.nodes) > idx + 1
                and self.nodes[idx + 1].content_category in self.SKIP):
                continue

            # If this node is in a category that should be skipped
            if node.content_category in self.SKIP:
                continue

            # If this is a title, see if it's the right heading level
            if node.node_type ==ContentNodeType.TITLE and previous_node:
                if previous_heading == None:
                    node.tag = 'h2'
                    setval.append(node)
                    previous_heading = node
                else:
                    if previous_heading.content_category == node.content_category:
                        node.increment_title_tag(previous_heading)
                        setval.append(node)
                        previous_heading = node

            # By default, just add the node
            setval.append(node)

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
