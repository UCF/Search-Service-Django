from django.core.management.base import BaseCommand, CommandError
from research.models import ResearchWork, Researcher, ResearcherEducation

from django.core.management.base import BaseCommand, CommandError

import settings
import requests

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

        self.records = Researcher.objects.all()
        self.orcid_base_url = settings.ORCID_BASE_API_URL
        self.headers = {
            'Accept': 'application/json'
        }

        self.__update_meta()

    def __update_meta(self):
        self.progress_bar = ChargingBar(
            'Updating researcher meta...',
            max=self.records.count()
        )

        for researcher in self.records:
            self.__update_education(researcher)
            self.__update_works(researcher)
            self.progress_bar.next()

        self.print_stats()

    def __update_education(self, researcher):
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
            return

        for education in education_data['education-summary']:
            self.edu_records_processed += 1

            # Wrap all the required fields in a try/except
            try:
                institution_name = education['organization']['name']
                role_name = education['role-title']
                put_code = education['put-code']
            except (KeyError, TypeError):
                # Can't add if any of these are missing
                self.edu_records_skipped += 1
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

                    self.edu_records_updated += 1
                except:
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
                    self.edu_records_error += 1


    def __update_works(self, researcher):
        works_url = '{0}{1}/works'.format(
            self.orcid_base_url,
            researcher.orcid_id
        )

        try:
            works_data = self.__request_records(works_url)
        except:
            works_data = None

        if works_data is None:
            return

        for work in works_data['group']:
            self.work_records_processed += 1
            # Make sure we have summary data
            try:
                summary = work['work-summary'][0]
            except (KeyError, ValueError, TypeError):
                # There's no work summary, continue
                self.work_records_skipped += 1
                continue

            # Get all required fields
            try:
                title = summary['title']['title']['value']
                work_type = summary['type']
                # Let's do some custom work on the publish date for these

                publish_date = self.__format_orcid_date(summary['publication-date'])
                put_code = summary['put-code']
            except (KeyError, ValueError, TypeError):
                self.work_records_skipped += 1
                continue

            try:
                subtitle = summary['title']['subtitle']['value'] \
                    if summary['title']['subtitle'] != 'None' \
                    else None
            except:
                subtitle = None

            if put_code is None or publish_date is None:
                self.work_records_skipped += 1
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
                    existing.work_type = work_type

                    existing.save()

                    self.work_records_updated += 1
                except:
                    self.work_records_error += 1
            else:
                try:
                    ResearchWork.objects.create(
                        researcher=researcher,
                        title=title,
                        subtitle=subtitle,
                        publish_date=publish_date,
                        work_type=work_type,
                        work_put_code=put_code
                    )

                    self.work_records_created += 1
                except:
                    self.work_records_error += 1


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
