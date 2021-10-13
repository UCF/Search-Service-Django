from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from research.models import Researcher
from research.models import Article
from research.models import Book
from research.models import BookChapter
from research.models import Grant
from research.models import HonorificAward
from research.models import Patent
from research.models import ClinicalTrial

from teledata.models import Staff

import settings
import requests
from dateutil import parser

import threading, queue

from progress.bar import ChargingBar

class Command(BaseCommand):
    help = 'Imports researchers from Academic Analytics'

    def add_arguments(self, parser):
        """
        Define the command line arguments using argparse
        """
        super().add_arguments(parser)

        parser.add_argument(
            '--api-url',
            dest='aa_api_url',
            type=str,
            help='The URL of the Academic Analytics API Endpoint',
            default=settings.ACADEMIC_ANALYTICS_API_URL,
            required=False
        )

        parser.add_argument(
            '--api-key',
            dest='aa_api_key',
            type=str,
            help='The API Key for the Academic Analytics API Endpoint',
            default=settings.ACADEMIC_ANALYTICS_API_KEY,
            required=False
        )


    def handle(self, *args, **options):
        """
        Main entry function for the command.
        All execution logic is handled here.
        """
        self.aa_api_url = self.__trailingslashit(options['aa_api_url'])
        self.aa_api_key = options['aa_api_key']
        self.max_threads = settings.RESEARCH_MAX_THREADS

        self.processed = 0
        self.created = 0
        self.updated = 0
        self.removed = 0
        self.skipped_no_empl = 0
        self.skipped_no_match = 0

        self.books_updated = 0
        self.books_created = 0
        self.articles_updated = 0
        self.articles_created = 0
        self.chapters_updated = 0
        self.chapters_created = 0
        self.confs_updated = 0
        self.confs_created = 0
        self.grants_updated = 0
        self.grants_created = 0
        self.awards_updated = 0
        self.awards_created = 0
        self.patents_updated = 0
        self.patents_created = 0
        self.trials_updated = 0
        self.trials_created = 0

        self.researchers_to_process = queue.Queue()

        self.__get_researchers()
        self.__process_research()

    def __get_researchers(self):
        url = 'person/list/'
        people = self.__request_resource(url)

        for person in people:
            self.processed += 1

            if person['ClientFacultyId'] == '':
                self.skipped_no_empl += 1
                continue

            try:
                staff = Staff.objects.get(employee_id=person['ClientFacultyId'].strip())
            except:
                self.skipped_no_match += 1
                continue

            orcid = person['ORCID'] if person['ORCID'] != '' else None
            aa_person_id = person['PersonId']

            researcher = None

            researcher = Researcher.objects.filter(
                Q(aa_person_id=aa_person_id)|
                Q(teledata_record=staff)
            )

            if researcher.count() > 1:
                # Remove those extra records
                extra_records = researcher[1:]
                for record in extra_records:
                    record.delete()
                    self.removed += 1

                researcher = researcher.first()
                researcher.aa_person_id = aa_person_id
                researcher.ordid_id = orcid
                researcher.teledata_record = staff
                researcher.save()
                self.updated += 1
            else:
                researcher = Researcher(
                    aa_person_id=aa_person_id,
                    orcid_id=orcid,
                    teledata_record=staff
                )
                researcher.save()
                self.created += 1

            self.researchers_to_process.put(researcher)

    def __process_research(self):
        self.progress_bar = ChargingBar(
            'Processing research...',
            max=self.researchers_to_process.qsize()
        )

        self.mt_lock = threading.Lock()

        for _ in range(self.max_threads):
            threading.Thread(target=self.get_researcher_research, daemon=True).start()

        self.researchers_to_process.join()

    def get_researcher_research(self):
        while True:
            try:
                researcher = self.researchers_to_process.get()

                with self.mt_lock:
                    self.progress_bar.next()

                # Let's get some articles!
                request_url = f'person/{researcher.aa_person_id}/articles/'
                articles = self.__request_resource(request_url)

                for article in articles:
                    try:
                        existing_article = Article(aa_article_id=article['ArticleId'])
                        existing_article.researcher = researcher
                        existing_article.article_title = article['ArticleTitle']
                        existing_article.journal_name = article['JournalName']
                        existing_article.article_year = article['ArticleYear']
                        existing_article.journal_volume = article['JournalVolume'] or None
                        existing_article.journal_issue = article['JournalIssue'] or None
                        existing_article.first_page = article['JournalFirstPage'] or None
                        existing_article.last_page = article['JournalLastPage'] or None
                        existing_article.save()

                        with self.mt_lock:
                            self.articles_updated += 1

                    except Article.DoesNotExist:
                        article = Article(
                            researcher=researcher,
                            aa_article_id=article['ArticleId'],
                            article_title=article['ArticleTitle'],
                            journal_name=article['JournalName'],
                            article_year=article['ArticleYear'],
                            journal_volume=article['JournalVolume'] or None,
                            journal_issue=article['JournalIssue'] or None,
                            first_page=article['JournalFirstPage'] or None,
                            last_page=article['JournalLastPage'] or None
                        )

                        article.save()

                        with self.mt_lock:
                            self.articles_created += 1

                    except:
                        self.stderr.write(f'There was an error creating the article {article["ArticleTitle"]}')

                # Let's get some books!
                request_url = f'person/{researcher.aa_person_id}/books/'
                books = self.__request_resource(request_url)

                for book in books:
                    try:
                        existing_book = Book.objects.get(aa_book_id=book['BookId'], researcher=researcher)
                        existing_book.isbn = book['Isbn']
                        existing_book.book_title = book['BookTitle']
                        existing_book.bisac = book['Bisac']
                        existing_book.publisher_name = book['PublisherName']
                        existing_book.publish_date = parser.parse(book['PublishDate'])
                        existing_book.save()

                        with self.mt_lock:
                            self.books_updated += 1
                    except Book.DoesNotExist:
                        book = Book(
                            researcher=researcher,
                            aa_book_id=book['BookId'],
                            isbn=book['Isbn'],
                            book_title=book['BookTitle'],
                            bisac=book['Bisac'],
                            publisher_name=book['PublisherName'],
                            publish_date=parser.parse(book['PublishDate'])
                        )
                        book.save()

                        with self.mt_lock:
                            self.books_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the book {book["BookTitle"]}')

            finally:
                self.researchers_to_process.task_done()

    def __trailingslashit(self, url):
        """
        Ensures the URL has a trailing slash
        """
        if url.endswith('/'):
            return url
        else:
            return f"{url}/"

    def __request_resource(self, url):
        """
        Helper function for requesting a resource
        from Academic Analytics. This will append
        the apikey header onto the request before
        making the request and returning a parsed
        JSON object.
        """
        request_url = f'{self.aa_api_url}{self.__trailingslashit(url)}'

        headers = {
            'Accept': 'application/json',
            'apikey': self.aa_api_key
        }

        response = requests.get(request_url, headers=headers)

        if response.ok:
            try:
                return response.json()
            except Exception as e:
                raise e
        else:
            raise Exception(f'There was a problem requesting the following URL: {url}')
