from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from queue import Queue
from threading import Thread
import requests
from urllib.parse import urlparse

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

    def handle(self, *args, **options):
        self.keywords = options['keywords']
        self.keywords_raw = self.keywords
        self.email = options['email']
        self.urls_to_process = Queue()
        self.results_queue = Queue()

        self.process_bing_results()
        self.crawl_pages()

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

        last_response = results['webPages']['value']

        while good_response:
            params['offset'] = params['count'] * idx
            response = requests.get(settings.BING_SEARCH_API_BASE, headers=headers, params=params)
            good_response = response.status_code >= 200 < 400
            results = response.json()
            if results['webPages']['value'] == last_response:
                break

            self.process_results(results)
            last_response = results['webPages']['value']
            idx += 1


    def process_results(self, results):
        for item in results['webPages']['value']:
            self.urls_to_process.put(item['url'])

    def quote_it(self, keyword):
        result = ''

        if not keyword.startswith('\"'):
            result = "\"" + keyword

        if not keyword.endswith('\"'):
            result += '\"'

        return result

    def worker(self, keywords, x):
        while True:
            try:
                url = self.urls_to_process.get_nowait()
            except:
                return
            try:
                response = requests.get(url, timeout=5)
            except:
                self.urls_to_process.task_done()
                continue

            if response.status_code < 200 >= 400:
                self.urls_to_process.task_done()
                continue

            result = {
                'url': url,
                'parts': urlparse(url),
                'keywords': []
            }

            content = response.text
            for keyword in keywords:
                result['keywords'].append({
                    'keyword': keyword,
                    'count': content.count(keyword)
                })

            self.results_queue.put(result)
            self.urls_to_process.task_done()


    def crawl_pages(self):
        threads = []

        for x in range(20):
            threads.append(
                Thread(
                    target=self.worker,
                    args=(self.keywords_raw, x),
                    daemon=True
                ).start()
            )

        self.urls_to_process.join()

        while True:
            result = self.results_queue.get_nowait()

            print(result)

            if self.results_queue.empty():
                break

        print("All done")
