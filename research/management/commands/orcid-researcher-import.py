from django.core.management.base import BaseCommand, CommandError
from research.models import Researcher
from teledata.models import Staff

from django.db.models import Q

import settings
import requests
import math
import pprint

from progress.bar import ChargingBar

class Command(BaseCommand):
    help = 'Imports researcher records from ORCID'

    processed = 0
    created = 0
    updated = 0
    error = 0

    orcid_ids_to_import = []

    def add_arguments(self, parser):
        """
        Define the command line arguments using argparse
        """
        parser.add_argument(
            '--orcid-api-url',
            dest='orcid_url',
            type=str,
            help='The URL of the ORCID API',
            default=settings.ORCID_BASE_API_URL,
            required=False
        )

        parser.add_argument(
            '--grid-id',
            dest='grid_id',
            type=str,
            help='The GRID ID of the institution to search for researchers',
            default=None,
            required=False
        )

        parser.add_argument(
            '--institution-name',
            dest='institution_name',
            type=str,
            help='The name of the institution to search for researchers',
            default=None,
            required=False
        )

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.
        """
        self.orcid_url = options['orcid_url']
        self.grid_id = None
        self.use_grid = False
        self.orcid_ids_to_import = []

        if options['grid_id'] is not None:
            self.grid_id = options['grid_id']
        elif hasattr( settings, 'INSTITUTION_GRID_ID' ) and settings.INSTITUTION_GRID_ID is not None:
            self.grid_id = settings.INSTITUTION_GRID_ID

        self.institution_name = options['institution_name']

        if self.grid_id is None and self.institution_name is None:
            raise CommandError('Either --grid-id or --insitution-name must be specified.')

        if self.grid_id is not None:
            self.use_grid = True

        self.get_orcid_ids()
        self.match_teledata_records()
        self.print_stats()

    def get_orcid_ids(self):
        """
        Gather all the ORCID IDs for the provided
        institution GRID ID or name.
        """
        request_url = '{0}{1}'.format(
            settings.ORCID_BASE_API_URL,
            'search/'
        )

        params = {}
        headers = {
            'Accept': 'application/json'
        }

        if self.use_grid:
            params['q'] = 'grid-org-id:{0}'.format(self.grid_id)
        else:
            params['q'] = 'affiliation-org-name:("{0}")'.format(self.institution_name)

        data = self.__request_records(0, request_url, params, headers)

        for row in data['result']:
            self.orcid_ids_to_import.append(row['orcid-identifier']['path'])
            self.processed += 1

        self.total_records = data['num-found']
        total_pages = math.ceil(self.total_records / 100)
        current_page = 1

        while (current_page <= total_pages):
            data = self.__request_records(current_page, request_url, params, headers)

            for row in data['result']:
                self.orcid_ids_to_import.append(row['orcid-identifier']['path'])
                self.processed += 1

            current_page += 1

        self.stdout.write('Collected {0} of {1} ORCID records found...\n'.format(self.processed, self.total_records))


    def match_teledata_records(self):
        """
        Loop through the found ORCID IDs,
        gather more information and attempt
        to match them up with our teledata
        records.
        """
        headers = {
            'Accept': 'application/json'
        }

        self.progress_bar = ChargingBar(
            'Processing',
            max=len(self.orcid_ids_to_import)
        )

        for orcid_id in self.orcid_ids_to_import:
            self.progress_bar.next()
            try:
                Researcher.objects.get(
                    orcid_id=orcid_id
                )

                # Not really, but it makes for better
                # at-a-glance understanding
                self.updated += 1
                # Nothing to do, continue
                continue
            except Researcher.DoesNotExist:
                existing = None

            request_url = "{0}{1}".format(
                settings.ORCID_BASE_API_URL,
                orcid_id
            )

            data = self.__request_records(0, request_url, {}, headers)

            try:
                first_name = data['person']['name']['given-names']['value']
                last_name = data['person']['name']['family-name']['value']
            except (KeyError, TypeError):
                self.stdout.write("Unable to get first or last name from record.\n")
                self.error += 1
                continue

            try:
                person = Staff.objects.get(
                    Q(
                        first_name__iexact=first_name,
                        last_name__iexact=last_name
                    )
                )

                created = Researcher.objects.create(
                    orcid_id=orcid_id,
                    teledata_record=person
                )

                if created:
                    self.created += 1

            except Staff.DoesNotExist:
                continue
                # self.stderr.write('Cannot find match for {0} {1}\n'.format(first_name, last_name))
            except Staff.MultipleObjectsReturned:
                continue
                # self.stderr.write('Well... whoops... There is more than one person with the name {0} {1}'.format(first_name, last_name))


    def __request_records(self, page_num, request_url, params, headers):
        """
        Private helper method for retrieving ORCID records
        """
        if page_num != 0:
            params['start'] = page_num * 100

        response = requests.get(request_url, params, headers=headers)

        if not response.ok:
            raise CommandError("There was an error retriving the results from ORCID")

        try:
            data = response.json()
        except ValueError as ve:
            raise CommandError("Unable to parse JSON response from ORCID: {0}".format(ve))

        return data

    def print_stats(self):
        stats = """
Processed : {0}
Created   : {1}
Updated   : {2}
Errors    : {3}

        """.format(
            self.processed,
            self.created,
            self.updated,
            self.error
        )

        self.stdout.write(stats)
