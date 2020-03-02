from django.core.management.base import BaseCommand, CommandError
import settings
import logging

from urlparse import urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Scrapes Google Scholars for data related to UCF researchers.'
    base_url = ''
    org_id = ''

    parsing_pages = True
    next_url = None

    def build_params(self):
        """
        Builds a parameter array for pulling authors
        """
        params = {
            'view_op': 'view_org',
            'hl'     : 'en',
            'org'    : self.org_id
        }

        return params

    def get_next_url(self, next_button):
        """
        Parses the html of the next button on the page
        and tries to coerce a working url out of it!
        """
        # Get the onclick command
        if next_button and next_button.has_attr('onclick'):
            onclick = next_button['onclick']
        else:
            self.parsing_pages = False
            return None

        # If the string starts with the window.location string
        # remove that string, the first quote and
        # the last quote
        if onclick.startswith('window.location=\''):
            onclick = onclick[len('window.location=\''):-1].replace('\\x3d', '=').replace('\\x26', '&')
            url = urlparse(self.base_url + onclick)
            onclick = url.geturl()

        return onclick

    def parse_page(self, content):
        """
        Parses a single webpage of authors. Usually,
        this will be 10 authors and a next button.
        """
        soup = BeautifulSoup(content, 'html.parser')

        scholars = soup.find_all('div', {'class': 'gsc_1usr'})

        for idx, sc in enumerate(scholars, start=0):
            name_anchor = sc.find('h3', {'class': 'gs_ai_name'}).find('a')
            name = name_anchor.text
            link = self.base_url + name_anchor['href']
            link_parts = urlparse(link)
            link_params = parse_qs(link_parts.query)
            affiliantion = sc.find('div', {'class': 'gs_ai_aff'}).text

        next_button = soup.find('button', {'class': 'gs_btnPR'})

        if next_button:
            self.next_url = self.get_next_url(next_button)
        else:
            self.next_url = None
            self.parsing_pages = False

    def import_authors(self):
        """
        Controls the while loopingness of hopefully not breaking.
        Continues to parse through pages until a "next_url" cannot
        be parsed and then exits.
        """
        params = self.build_params()

        while (self.parsing_pages):
            if self.next_url:
                resp = requests.get(self.next_url)
            else:
                resp = requests.get(self.base_url + '/citations', params=params)

            if resp.status_code == 200:
                self.parse_page(resp.content)
            else:
                self.parsing_pages = False

    def handle(self, *args, **options):
        """
        Sets up the command and kicks it off.
        """
        self.base_url = settings.GOOGLE_SCHOLARS_BASE
        self.org_id = settings.GOOGLE_SCHOLARS_ORG

        self.import_authors()
