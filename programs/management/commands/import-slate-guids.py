from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import decimal
import itertools
import json
import logging
import mimetypes
import requests
import sys


class Command(BaseCommand):
    help = (
        'Imports unique identifiers for programs from Undergraduate '
        'or Graduate Studies\' Slate instances.'
    )

    programs = []
    programs_count = 0
    programs_matched = set()
    guid_data = []
    rows_matched_count = 0
    rows_skipped_count = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--graduate',
            type=bool,
            help='''\
            Set to True if this is an import of graduate
            GUID data
            ''',
            dest='graduate',
            default=False,
            required=False
        )
        parser.add_argument(
            '--verbose',
            help='Use verbose logging',
            action='store_const',
            dest='loglevel',
            const=logging.INFO,
            default=logging.WARNING,
            required=False
        )

    def handle(self, *args, **options):
        self.career = 'Graduate' if options['graduate'] is True else 'Undergraduate'
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        # Fetch all programs, by career:
        self.programs = Program.objects.filter(career__name=self.career)
        self.programs_count = len(self.programs)

        # Fetch GUID data:
        self.get_guid_data()

        # Assign GUIDs to existing programs:
        self.assign_guids()

        # Print results
        self.print_results()

    def get_guid_data(self):
        """
        Retrieves GUID data from an external Slate instance.
        """
        if self.career == 'Undergraduate':
            self.get_undergraduate_guid_data()
        else:
            self.get_graduate_guid_data()

    def get_undergraduate_guid_data(self):
        """
        Retrieves and sets undergraduate GUIDs.
        """
        # We don't have undergraduate GUIDs
        # right now--add logic later if we get any.
        return

    def get_graduate_guid_data(self):
        """
        Retrieves and sets graduate GUID data from
        Graduate Studies' Slate instance.
        """
        credentials = settings.GRADUATE_SLATE_ENDPOINTS['guids']

        try:
            response = requests.get(
                credentials['endpoint'],
                auth=(credentials['username'], credentials['password'])
            )
            response_str = response.text
            # Make their null values actually parse to `null` and not "NULL":
            response_str_cleaned = response_str.replace('"NULL"', 'null')
            response_json = json.loads(response_str_cleaned)
        except Exception as e:
            logging.warning(
                '\nError retrieving Graduate GUID data: {0}'
                .format(e)
            )
        else:
            self.guid_data = response_json['row']

    def assign_guids(self):
        """
        Handles assignment of GUIDs to programs by career type.
        """
        # If we have new GUID data to process, delete any existing data.
        # Otherwise, abort this process:
        if len(self.guid_data):
            print((
                (
                    'Deleting all existing GUID values '
                    'for {0} Programs.'
                ).format(
                    self.career
                )
            ))

            # Clear existing GUIDs on all programs in self.programs:
            if self.programs_count:
                if self.career == 'Undergraduate':
                    # Add logic here if/when we get access to
                    # undergraduate Slate IDs:
                    pass
                else:
                    self.programs.update(
                        graduate_slate_id=None
                    )
            else:
                print (
                    'No programs to process. Assignment of new '
                    'GUIDs aborted.'
                )
                return
        else:
            print (
                'No GUID data to process. Assignment of new '
                'GUIDs aborted.'
            )
            return

        # Run career-specific GUID imports:
        if self.career == 'Undergraduate':
            self.assign_undergraduate_guids()
        else:
            self.assign_graduate_guids()

    def assign_undergraduate_guids(self):
        """
        Handles assignment of GUIDs from `self.guid_data` for
        Undergraduate Programs.
        """
        return

    def assign_graduate_guids(self):
        """
        Handles assignment of GUIDs from `self.guid_data` for
        Graduate Programs.
        """
        career = Career.objects.get(name=self.career)

        for row in self.guid_data:
            plan_code = row['PLAN']
            subplan_code = row['SUBPLAN']
            guid = row['GUID']
            program = None

            # Make sure the program specified in this row of data
            # is valid before proceeding any further:
            try:
                program = Program.objects.get(
                    plan_code=plan_code,
                    subplan_code=subplan_code,
                    career=career
                )
            except Program.DoesNotExist:
                logging.warning(
                    (
                        'Cannot find existing {0} Program with plan '
                        'code "{1}" and subplan code "{2}" to '
                        'assign a GUID to. '
                        'Skipping GUID data row'
                    ).format(
                        self.career,
                        plan_code,
                        subplan_code
                    )
                )
                self.rows_skipped_count += 1
            else:
                program.graduate_slate_id = guid
                program.save()

                self.rows_matched_count += 1
                self.programs_matched.add(program)
                logging.info(
                    (
                        'Assigned {0} GUID "{1}" to program "{2}" '
                        '(plan code "{3}", subplan code "{4}")'
                    ).format(
                        self.career,
                        guid,
                        program.name,
                        program.plan_code,
                        program.subplan_code
                    )
                )

    def print_results(self):
        print((
            'Finished import of {0} Program GUID data.'
        ).format(self.career))

        if self.programs_count:
            print((
                'Assigned a GUID to {0}/{1} '
                'existing {2} Programs: {3: .0f} %'
            ).format(
                len(self.programs_matched),
                self.programs_count,
                self.career,
                float(len(self.programs_matched)) /
                float(self.programs_count) * 100
            ))
        else:
            print('No programs were assigned a GUID.')

        if len(self.guid_data):
            print((
                'Matched {0}/{1} rows of {2} GUID data: {3: .0f} %'
            ).format(
                self.rows_matched_count,
                len(self.guid_data),
                self.career,
                float(self.rows_matched_count) /
                float(len(self.guid_data)) * 100
            ))
        else:
            print('No GUID data was processed.')

        print((
            'Skipped {0} rows of {1} GUID data.'
        ).format(
            self.rows_skipped_count,
            self.career
        ))
