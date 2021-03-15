from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import EmailMessage

import requests
import csv
import io

import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from core.crawler import KeywordSpider

class Command(BaseCommand):
    help = 'Generates a report with a count of keywords for UCF web pages.'

    def add_arguments(self, parser):
        parser.add_argument(
            'keywords',
            type=str,
            nargs='+',
            help='The keywords to run the report with.'
        )

        parser.add_argument(
            '--email',
            type=str,
            dest='email',
            help='The email to send the report to.',
            required=False
        )

        parser.add_argument(
            '--outfile',
            type=str,
            dest='outfile',
            help='The destination of the csv file.',
            default='./keywords.csv'
        )

        parser.add_argument(
            '--result-threshold',
            type=int,
            dest='result_threshold',
            help='The number of results to limit the search to.',
            default=None
        )

    def handle(self, *args, **options):
        self.keywords = options['keywords']
        self.keywords_raw = self.keywords
        self.email = options['email']
        self.filepath = options['outfile']
        self.limit = options['result_threshold']
        self.urls_to_process = list()
        self.results = list()

        print("Fetching search results...")
        self.process_bing_results()
        print(f"Results found: {len(self.urls_to_process)}")
        print("Crawling pages...")
        self.crawl_pages()
        print("Organizing results...")
        self.organize_results()
        print("Writing results")
        self.write_results()
        print("Emailing results...")
        self.send_report()

        print("All done")

    def process_bing_results(self):
        if not settings.MICROSOFT_AZURE_API_KEY or not settings.BING_SEARCH_API_BASE:
            raise CommandError("The MICROSOFT_AZURE_API_KEY and BING_SEARCH_API_BASE must be configured in the settings_local.py")

        # Make sure the keywords are wrapped in quotes
        self.keywords = list(map(self.quote_it, self.keywords))

        keyword_string = "+".join(self.keywords)

        keyword_string += " site:ucf.edu"

        headers = {
            "Ocp-Apim-Subscription-Key": settings.MICROSOFT_AZURE_API_KEY
        }

        params = {
            "q": keyword_string,
            "count": 10,
            "offset": 0,
            'responseFilter': 'Webpages',
            "textFormat": "Raw"
        }

        response = requests.get(settings.BING_SEARCH_API_BASE, headers=headers, params=params)
        good_response = response.status_code >= 200 < 400
        results = response.json()
        self.process_results(results)
        idx = 1

        if 'webPages' in results:
            last_response = results['webPages']['value']
        else:
            good_response = False
            return

        while good_response:
            params['offset'] = params['count'] * idx
            response = requests.get(settings.BING_SEARCH_API_BASE, headers=headers, params=params)
            good_response = response.status_code >= 200 < 400
            if not good_response:
                break
            results = response.json()
            if not 'webPages' in results or results['webPages']['value'] == last_response:
                break

            self.process_results(results)
            last_response = results['webPages']['value']
            idx += 1

            if self.limit and len(self.urls_to_process) >= self.limit:
                break;


    def process_results(self, results):
        if not 'webPages' in results:
            return

        for item in results['webPages']['value']:
            self.urls_to_process.append(item['url'])

    def quote_it(self, keyword):
        result = ''

        if not keyword.startswith('\"'):
            result = "\"" + keyword

        if not keyword.endswith('\"'):
            result += '\"'

        return result


    def append_result(self, signal, sender, item, response, spider):
        self.results.append(item)

    def crawl_pages(self):
        self.fields = ['domain', 'url']

        for keyword in self.keywords_raw:
            self.fields.append(f"\"{keyword}\" count")

        process = CrawlerProcess(
            settings={
                'items.json': {
                    'format': 'json',
                    'fields': self.fields
                },
            },
        )

        dispatcher.connect(self.append_result, signal=signals.item_passed)

        process.crawl(KeywordSpider, urls=self.urls_to_process, keywords=self.keywords_raw)
        process.start()


    def organize_results(self):
        self.domains = []

        for result in self.results:
            domain = next((x for x in self.domains if x['domain'] == result['domain']), None)

            if not domain:
                domain = {}

                for f in self.fields:
                    domain[f] = result[f]
                self.domains.append(domain)
            else:
                for f in self.fields[len(self.keywords_raw)*-1:]:
                    domain[f] += result[f]

    def write_results(self):
        self.domain_report = None
        self.raw_report = None

        with io.StringIO() as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writeheader()

            for result in self.domains:
                writer.writerow(result)
            # Read the contents into a variable so the stream can close
            self.domain_report = csvfile.getvalue()


        with io.StringIO() as csvfile:

            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writeheader()

            for result in self.results:
                writer.writerow(result)
            # Read the contents into a variable so the stream can close
            self.raw_report = csvfile.getvalue()

    def send_report(self):
        body = "Attached are the per domain and raw data reports for the following keywords:"

        for keyword in self.keywords_raw:
            body += f"\n     - {keyword}"

        message = EmailMessage(
            'Keyword report completed.',
            body,
            'webcom@ucf.edu',
            [self.email]
        )
        message.attach('keyword_domain_report.csv', self.domain_report, 'text/csv')
        message.attach('keyword_raw_report.csv', self.raw_report, 'text/csv')

        message.send()
