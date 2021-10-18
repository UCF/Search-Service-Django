from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from research.models import ConferenceProceeding, ResearchWork, Researcher
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

        parser.add_argument(
            '--force-update',
            action='store_true',
            dest='force_update',
            help='Forces all researchers and research to be reimported',
            default=False
        )


    def handle(self, *args, **options):
        """
        Main entry function for the command.
        All execution logic is handled here.
        """
        self.aa_api_url = self.__trailingslashit(options['aa_api_url'])
        self.aa_api_key = options['aa_api_key']
        self.force_update = options['force_update']
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

        if self.force_update:
            self.__remove_all_records()

        self.__get_researchers()
        self.__process_research()
        self.__print_stats()

    def __remove_all_records(self):
        """
        Deletes all researchers
        """
        self.stdout.write(self.style.WARNING(f"Removing {Researcher.objects.count()} researchers"))
        Researcher.objects.all().delete()

        self.stdout.write(self.style.WARNING(f"Removing {ResearchWork.objects.count()} research objects"))
        ResearchWork.objects.all().delete()

    def __get_researchers(self):
        url = 'person/list/'
        people = self.__request_resource(url)
        processed_records = []

        for person in people:
            self.processed += 1

            if person['ClientFacultyId'] == '':
                self.skipped_no_empl += 1
                continue

            try:
                employee_id = person['ClientFacultyId'].zfill(7)
                staff = Staff.objects.get(employee_id=employee_id)
            except:
                self.skipped_no_match += 1
                continue

            orcid = person['ORCID'] if person['ORCID'] != '' else None
            aa_person_id = person['PersonId']

            researcher = None

            try:
                researcher = Researcher.objects.get(aa_person_id=aa_person_id)
                researcher.orcid_id = orcid
                researcher.teledata_record = staff
                researcher.save()

                self.updated += 1
            except Researcher.DoesNotExist:
                researcher = Researcher(
                    aa_person_id=aa_person_id,
                    orcid_id=orcid,
                    teledata_record=staff
                )
                researcher.save()
                self.created += 1
            except Researcher.MultipleObjectsReturned:
                # Delete all the matching records and start new
                researchers = Researcher.objects.filter(aa_person_id=aa_person_id)
                self.removed += researchers.count()
                researchers.delete()

                researcher = Researcher(
                    aa_person_id=aa_person_id,
                    orcid_id=orcid,
                    teledata_record=staff
                )
                researcher.save()
                self.created += 1

            processed_records.append(researcher.id)
            self.researchers_to_process.put(researcher)

        stale_records = Researcher.objects.filter(~Q(pk__in=processed_records))
        self.removed += stale_records.count()
        stale_records.delete()

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
                        existing_article = Article.objects.get(aa_article_id=article['ArticleId'], researcher=researcher)
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
                        new_article = Article(
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

                        new_article.save()

                        with self.mt_lock:
                            self.articles_created += 1

                    except Exception as e:
                        self.stderr.write(f'There was an error creating the article {article["ArticleTitle"]}, {e}')

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
                        new_book = Book(
                            researcher=researcher,
                            aa_book_id=book['BookId'],
                            isbn=book['Isbn'],
                            book_title=book['BookTitle'],
                            bisac=book['Bisac'],
                            publisher_name=book['PublisherName'],
                            publish_date=parser.parse(book['PublishDate'])
                        )
                        new_book.save()

                        with self.mt_lock:
                            self.books_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the book {book["BookTitle"]}')

                # Let's get some book chapters!
                request_url = f'person/{researcher.aa_person_id}/bookchapters/'
                chapters = self.__request_resource(request_url)

                for chapter in chapters:
                    try:
                        existing_chapter = BookChapter.objects.get(aa_book_id=chapter['BookId'], researcher=researcher)
                        existing_chapter.isbn = chapter['Isbn']
                        existing_chapter.book_title = chapter['BookTitle']
                        existing_chapter.chapter_title = chapter['ChapterTitle']
                        existing_chapter.bisac = chapter['Bisac']
                        existing_chapter.publisher_name = chapter['PublisherName']
                        existing_chapter.publish_year = chapter['PublishYear']
                        existing_chapter.publish_date = parser.parse(chapter['PublishDate'])
                        existing_chapter.save()

                        with self.mt_lock:
                            self.chapters_updated += 1
                    except BookChapter.DoesNotExist:
                        new_chapter = BookChapter(
                            researcher=researcher,
                            aa_book_id=chapter['BookId'],
                            isbn=chapter['Isbn'],
                            book_title=chapter['BookTitle'],
                            chapter_title=chapter['ChapterTitle'],
                            bisac=chapter['Bisac'],
                            publisher_name=chapter['PublisherName'],
                            publish_year=chapter['PublishYear'],
                            publish_date=parser.parse(chapter['PublishDate'])
                        )
                        new_chapter.save()

                        with self.mt_lock:
                            self.chapters_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the book chapter {chapter["ChapterTitle"]}')

                # Let's get some conference proceedings!
                request_url = f'person/{researcher.aa_person_id}/proceedings/'
                proceedings = self.__request_resource(request_url)

                for proceeding in proceedings:
                    try:
                        existing_pro = ConferenceProceeding.objects.get(aa_article_id=proceeding['ArticleId'], researcher=researcher)
                        existing_pro.proceeding_title = proceeding['ProceedingTitle']
                        existing_pro.journal_name = proceeding['JournalName']
                        existing_pro.article_year = proceeding['ArticleYear']
                        existing_pro.journal_volume = proceeding['JournalVolume']
                        existing_pro.journal_issue = proceeding['JournalIssue']
                        existing_pro.first_page = proceeding['JournalFirstPage']
                        existing_pro.last_page = proceeding['JournalLastPage']
                        existing_pro.save()

                        with self.mt_lock:
                            self.confs_updated += 1
                    except ConferenceProceeding.DoesNotExist:
                        new_pro = ConferenceProceeding(
                            researcher=researcher,
                            aa_article_id=proceeding['ArticleId'],
                            proceeding_title=proceeding['ProceedingTitle'],
                            journal_name=proceeding['JournalName'],
                            article_year=proceeding['ArticleYear'],
                            journal_volume=proceeding['JournalVolume'],
                            journal_issue=proceeding['JournalIssue'],
                            first_page=proceeding['JournalFirstPage'],
                            last_page=proceeding['JournalLastPage']
                        )
                        new_pro.save()

                        with self.mt_lock:
                            self.confs_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the conference proceeding {proceeding["ProceedingTitle"]}')

                # Let's get some grants!
                request_url = f'person/{researcher.aa_person_id}/grants/'
                grants = self.__request_resource(request_url)

                for grant in grants:
                    try:
                        existing_grant = Grant.objects.get(aa_grant_id=grant['GrantId'], researcher=researcher)
                        existing_grant.agency_name = grant['AgencyName']
                        existing_grant.grant_name = grant['GrantName']
                        existing_grant.duration_years = grant['DurationInYears']
                        existing_grant.start_date = parser.parse(grant['StartDate'])
                        existing_grant.end_date = parser.parse(grant['EndDate'])
                        existing_grant.full_name = grant['FullName']
                        existing_grant.total_dollars = grant['TotalDollars']
                        existing_grant.is_research = bool(grant['IsResearch'])
                        existing_grant.principle_investigator = True if grant['AwardeeTypeCode'] == 'PI' else False
                        existing_grant.save()

                        with self.mt_lock:
                            self.grants_updated += 1

                    except Grant.DoesNotExist:
                        new_grant = Grant(
                            researcher=researcher,
                            aa_grant_id=grant['GrantId'],
                            agency_name=grant['AgencyName'],
                            grant_name=grant['GrantName'],
                            duration_years=grant['DurationInYears'],
                            start_date=parser.parse(grant['StartDate']),
                            end_date=parser.parse(grant['EndDate']),
                            full_name=grant['FullName'],
                            total_dollars=grant['TotalDollars'],
                            is_research=bool(grant['IsResearch']),
                            principle_investigator=True if grant['AwardeeTypeCode'] == 'PI' else False
                        )
                        new_grant.save()

                        with self.mt_lock:
                            self.grants_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the grant {grant["GrantTitle"]}')

                # Let's get some awards!
                request_url = f'person/{researcher.aa_person_id}/awards/'
                awards = self.__request_resource(request_url)

                for award in awards:
                    try:
                        existing_award = HonorificAward.objects.get(aa_award_id=award['AwardId'], researcher=researcher)
                        existing_award.governing_society_name = award['AwardGoverningSocietyName']
                        existing_award.award_name = award['AwardName']
                        existing_award.award_received_name = award['AwardReceivedName']
                        existing_award.award_received_year = award['AwardReceivedAwardYear']
                        existing_award.save()

                        with self.mt_lock:
                            self.awards_updated += 1
                    except HonorificAward.DoesNotExist:
                        new_award = HonorificAward(
                            researcher=researcher,
                            aa_award_id=award['AwardId'],
                            governing_society_name=award['AwardGoverningSocietyName'],
                            award_name=award['AwardName'],
                            award_received_name=award['AwardReceivedName'],
                            award_received_year=award['AwardReceivedAwardYear']
                        )
                        new_award.save()

                        with self.mt_lock:
                            self.awards_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the award {award["AwardName"]}')

                # Let's get some patents!
                request_url = f'person/{researcher.aa_person_id}/patents/'
                patents = self.__request_resource(request_url)

                for patent in patents:
                    try:
                        existing_patent = Patent.objects.get(patent_id=patent['PatentId'], researcher=researcher)
                        existing_patent.patent_title = patent['PatentTitle']
                        existing_patent.patent_type = patent['PatentType']
                        existing_patent.patent_kind = patent['PatentKind']
                        existing_patent.patent_date = parser.parse(patent['PatentDate'])
                        existing_patent.country = patent['Country']
                        existing_patent.claims = patent['NumClaims']
                        existing_patent.abstract = patent['Abstract']
                        existing_patent.save()

                        with self.mt_lock:
                            self.patents_updated += 1
                    except Patent.DoesNotExist:
                        new_patent = Patent(
                            researcher=researcher,
                            patent_id=patent['PatentId'],
                            patent_title=patent['PatentTitle'],
                            patent_type=patent['PatentType'],
                            patent_kind=patent['PatentKind'],
                            patent_date=parser.parse(patent['PatentDate']),
                            country=patent['Country'],
                            claims=patent['NumClaims'],
                            abstract=patent['Abstract']
                        )
                        new_patent.save()

                        with self.mt_lock:
                            self.patents_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the patent {patent["PatentTitle"]}')

                # Let's get some trials!
                request_url = f'person/{researcher.aa_person_id}/clinicaltrials/'
                trials = self.__request_resource(request_url)

                for trial in trials:
                    try:
                        existing_trial = ClinicalTrial.objects.get(nct_id=trial['NCTId'], researcher=researcher)
                        existing_trial.title = trial['Title']
                        existing_trial.start_date = parser.parse(trial['StartDate'])
                        existing_trial.completion_date = parser.parse(trial['CompletionDate']) if trial['CompletionDate'] != '' else None
                        existing_trial.study_type = trial['StudyType']
                        existing_trial.sponsor = trial['Sponsor']
                        existing_trial.allocation = trial['Allocation']
                        existing_trial.phase = trial['Phase']
                        existing_trial.recruitment_status = trial['RecruitmentStatus']
                        existing_trial.investigators = trial['Investigators']
                        existing_trial.save()

                        with self.mt_lock:
                            self.trials_updated += 1
                    except ClinicalTrial.DoesNotExist:
                        new_trial = ClinicalTrial(
                            researcher=researcher,
                            nct_id=trial['NCTId'],
                            title=trial['Title'],
                            start_date=parser.parse(trial['StartDate']),
                            completion_date=parser.parse(trial['CompletionDate']) if trial['CompletionDate'] != '' else None,
                            study_type=trial['StudyType'],
                            sponsor=trial['Sponsor'],
                            allocation=trial['Allocation'],
                            phase=trial['Phase'],
                            recruitment_status=trial['RecruitmentStatus'],
                            investigators=trial['Investigators']
                        )
                        new_trial.save()

                        with self.mt_lock:
                            self.trials_created += 1
                    except:
                        self.stderr.write(f'There was an error creating the clinical trial {trial["Title"]}')

            finally:
                self.researchers_to_process.task_done()

    def __print_stats(self):
        """
        Prints the stats from the import to the console
        """

        msg = f"""
Researchers
---------------------

Records Processed: {self.processed}
Records Created  : {self.created}
Records Updated  : {self.updated}
Records Removed  : {self.removed}

Records with no EmplId: {self.skipped_no_empl}
Records with no Match : {self.skipped_no_match}

Research
----------------------

Books Created        : {self.books_created}
Books Updated        : {self.books_updated}

Book Chapters Created: {self.chapters_created}
Book Chapters Updated: {self.chapters_updated}

Articles Created     : {self.articles_created}
Articles Updated     : {self.articles_updated}

Proceedings Created  : {self.confs_created}
Proceedings Updated  : {self.confs_updated}

Grants Created       : {self.grants_created}
Grants Updated       : {self.grants_updated}

Awards Created       : {self.awards_created}
Awards Updated       : {self.awards_updated}

Patents Created      : {self.patents_created}
Patents Updated      : {self.patents_updated}

Trials Created       : {self.trials_created}
Trials Updated       : {self.trials_updated}
        """

        self.stdout.write(self.style.SUCCESS(msg))

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
