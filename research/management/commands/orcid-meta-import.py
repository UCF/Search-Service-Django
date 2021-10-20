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

        self.max_threads = settings.RESEARCH_MAX_THREADS

        self.records = Researcher.objects.filter(orcid_id__isnull=False)
        self.orcid_base_url = settings.ORCID_BASE_API_URL
        self.headers = {
            'Accept': 'application/json'
        }

        self.education_queue = queue.Queue()

        self.mt_lock = threading.Lock()

        self.__update_meta()

    def __update_meta(self):
        self.education_threads = []

        self.education_pb = ChargingBar(
            'Updating researcher education...',
            max=self.records.count()
        )

        for _ in range(self.max_threads):
            threading.Thread(target=self.__update_education, daemon=True).start()


        for researcher in self.records:
            self.education_queue.put(researcher)

        # Let's take care of all the research at once
        self.education_queue.join()

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
"""

        self.stdout.write(stats)
