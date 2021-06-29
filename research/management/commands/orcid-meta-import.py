from django.core.management.base import BaseCommand, CommandError
from research.models import ResearchWork, Researcher, ResearcherEducation

from django.core.management.base import BaseCommand, CommandError

import settings
import requests
import threading, queue

from datetime import datetime

from progress.bar import ChargingBar

class Command(BaseCommand):
    help = 'Imports researcher meta values from ORCID'

    def add_arguments(self, parser):
        """
        Define the command line arguments using argparse
        """
        super().add_arguments(parser)

    def handle(self, *args, **options):
        # Initialize all of our stat counters
        self.edu_records_processed = 0
        self.edu_records_created = 0
        self.edu_records_updated = 0
        self.edu_records_skipped = 0
        self.edu_records_error = 0

        self.bio_records_processed = 0
        self.bio_records_created = 0
        self.bio_records_updated = 0
        self.bio_records_skipped = 0
        self.bio_records_error = 0

        self.work_records_processed = 0
        self.work_records_created = 0
        self.work_records_updated = 0
        self.work_records_skipped = 0
        self.work_records_error = 0

        self.max_threads = settings.RESEARCH_MAX_THREADS

        self.records = Researcher.objects.all()
        self.orcid_base_url = settings.ORCID_BASE_API_URL
        self.headers = {
            'Accept': 'application/json'
        }

        self.education_queue = queue.Queue()
        self.works_queue = queue.Queue()
        self.works_detail_queue = queue.Queue()

        self.mt_lock = threading.Lock()

        self.__update_meta()

    def __update_meta(self):
        self.education_threads = []
        self.works_threads = []
        self.work_detail_threads = []

        self.education_pb = ChargingBar(
            'Updating researcher education...',
            max=self.records.count()
        )

        self.works_pb = ChargingBar(
            'Gathering researcher works...',
            max=self.records.count()
        )

        for _ in range(self.max_threads):
            threading.Thread(target=self.__update_education, daemon=True).start()


        for researcher in self.records:
            self.education_queue.put(researcher)
            self.works_queue.put(researcher)

            # Works details get filled up during
            # the thread work of the __get_works_data
            # functions.

        # Let's take care of all the research at once
        self.education_queue.join()

        for _ in range(self.max_threads):
            threading.Thread(target=self.__get_works_data, daemon=True).start()

        self.works_queue.join()

        # Everything below is dependent on everything
        # above finishing. That's why none of the following
        # is declared until after the second queue.join()

        self.works_details_pb = ChargingBar(
            'Updating researcher works data...',
            max=self.works_detail_queue.qsize()
        )

        for _ in range(self.max_threads):
            threading.Thread(target=self.__process_works_details, daemon=True).start()

        self.works_detail_queue.join()

        self.print_stats()

    def __update_education(self):
        while True:
            researcher = self.education_queue.get()

            with self.mt_lock:
                self.education_pb.next()

            education_url = '{0}{1}/educations'.format(
                self.orcid_base_url,
                researcher.orcid_id
            )

            try:
                education_data = self.__request_records(education_url)
            except CommandError:
                education_data = None

            # Exit early if we didn't get any education data
            if education_data is None:
                self.education_queue.task_done()
                continue

            for education in education_data['education-summary']:
                with self.mt_lock:
                    self.edu_records_processed += 1

                # Wrap all the required fields in a try/except
                try:
                    institution_name = education['organization']['name']
                    role_name = education['role-title']
                    put_code = education['put-code']
                except (KeyError, TypeError):
                    # Can't add if any of these are missing
                    with self.mt_lock:
                        self.edu_records_skipped += 1
                    self.education_queue.task_done()
                    continue

                try:
                    department_name = education['department-name']
                except (KeyError, TypeError):
                    # We can live without a department_name.
                    department_name = None

                start_date = self.__format_orcid_date(education['start-date'])
                end_date = self.__format_orcid_date(education['end-date'])

                try:
                    existing = ResearcherEducation.objects.get(education_put_code=put_code)
                except ResearcherEducation.DoesNotExist:
                    existing = None

                if existing:
                    try:
                        existing.institution_name = institution_name
                        existing.start_date = start_date
                        existing.end_date = end_date
                        existing.department_name = department_name
                        existing.role_name = role_name
                        existing.save()

                        with self.mt_lock:
                            self.edu_records_updated += 1
                    except:
                        with self.mt_lock:
                            self.edu_records_error += 1
                else:
                    try:
                        ResearcherEducation.objects.create(
                            researcher=researcher,
                            institution_name=institution_name,
                            start_date=start_date,
                            end_date=end_date,
                            department_name=department_name,
                            role_name=role_name,
                            education_put_code=put_code
                        )
                    except:
                        with self.mt_lock:
                            self.edu_records_error += 1


            self.education_queue.task_done()


    def __get_works_data(self):
        while True:
            researcher = self.works_queue.get()

            with self.mt_lock:
                self.works_pb.next()

            works_url = '{0}{1}/works'.format(
                self.orcid_base_url,
                researcher.orcid_id
            )

            try:
                works_data = self.__request_records(works_url)
            except:
                works_data = None

            if works_data is None:
                self.works_queue.task_done()
                continue

            for work in works_data['group']:
                self.works_detail_queue.put((researcher, work,))

            self.works_queue.task_done()


    def __process_works_details(self):
        while True:
            researcher, work = self.works_detail_queue.get()

            with self.mt_lock:
                self.works_details_pb.next()

            with self.mt_lock:
                self.work_records_processed += 1
            # Make sure we have summary data
            try:
                summary = work['work-summary'][0]
            except (KeyError, ValueError, TypeError):
                # There's no work summary, continue
                with self.mt_lock:
                    self.work_records_skipped += 1
                self.works_detail_queue.task_done()
                continue



            # Get all required fields
            try:
                title = summary['title']['title']['value']
                work_type = summary['type']
                # Let's do some custom work on the publish date for these

                publish_date = self.__format_orcid_date(summary['publication-date'])
                put_code = summary['put-code']
            except (KeyError, ValueError, TypeError):
                with self.mt_lock:
                    self.work_records_skipped += 1
                self.works_detail_queue.task_done()
                continue

            work_details_url = '{0}{1}/works/{2}'.format(
                self.orcid_base_url,
                researcher.orcid_id,
                put_code
            );

            work_details = self.__request_records(work_details_url)

            if (work_details):
                try:
                    bt_str = work_details['bulk'][0]['work']['citation']['citation-value']
                except:
                    bt_str = None

            try:
                subtitle = summary['title']['subtitle']['value'] \
                    if summary['title']['subtitle'] != 'None' \
                    else None
            except:
                subtitle = None

            if put_code is None or publish_date is None:
                with self.mt_lock:
                    self.work_records_skipped += 1
                self.works_detail_queue.task_done()
                continue

            try:
                existing = ResearchWork.objects.get(work_put_code=put_code)
            except ResearchWork.DoesNotExist:
                existing = None

            if existing:
                try:
                    existing.title = title
                    existing.subtitle = subtitle
                    existing.publish_date = publish_date
                    existing.bibtex_string = bt_str
                    existing.work_type = work_type

                    existing.save()

                    with self.mt_lock:
                        self.work_records_updated += 1
                except:
                    with self.mt_lock:
                        self.work_records_error += 1
            else:
                try:
                    ResearchWork.objects.create(
                        researcher=researcher,
                        title=title,
                        subtitle=subtitle,
                        publish_date=publish_date,
                        bibtex_string = bt_str,
                        work_type=work_type,
                        work_put_code=put_code
                    )

                    with self.mt_lock:
                        self.work_records_created += 1
                except:
                    with self.mt_lock:
                        self.work_records_error += 1

            self.works_detail_queue.task_done()


    def __request_records(self, request_url, params={}):
        """
        Private helper method for retrieving ORCID records
        """
        response = requests.get(request_url, params, headers=self.headers)

        if not response.ok:
            return None

        try:
            data = response.json()
        except ValueError as ve:
            return None

        return data

    def __format_orcid_date(self, date_object):
        """
        ORCID returns dates in an interesting format, so this helper
        function will parse and error handle the conversion, returning
        None if anything does wrong
        """
        if not date_object:
            return None

        s_year  = None
        s_month = None
        s_day   = None

        if ('year' in date_object and
            date_object['year'] is not None and
            'value' in date_object['year']):
            s_year = date_object['year']['value']

        if ('month' in date_object and
            date_object['month'] is not None and
            'value' in date_object['month']):
            s_month = date_object['month']['value']

        if ('day' in date_object and
            date_object['day'] is not None and
            'value' in date_object['day']):
            s_day = date_object['day']['value']

        # No point in continuing if we don't
        # have at least a year
        if not s_year:
            return

        s_date = f"{s_year}"
        s_date += f"/{s_month}" if s_month is not None else f"/01"
        s_date += f"/{s_day}" if s_day is not None else f"/01"

        try:
            return datetime.strptime(s_date, '%Y/%m/%d')
        except ValueError as ve:
            return None


    def print_stats(self):
        stats = f"""
Education Records
------------------

Processed : {self.edu_records_processed}
Created   : {self.edu_records_created}
Updated   : {self.edu_records_updated}
Skipped   : {self.edu_records_skipped}
Errors    : {self.edu_records_error}


Research Records
------------------

Processed : {self.work_records_processed}
Created   : {self.work_records_created}
Updated   : {self.work_records_updated}
Skipped   : {self.work_records_skipped}
Errors    : {self.work_records_error}

        """

        self.stdout.write(stats)
