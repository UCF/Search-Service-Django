from django.core.management.base import BaseCommand, CommandError
from programs.models import *

from dateutil.parser import *
import decimal
import itertools
import json
import logging
import mimetypes
import requests
import sys


class Command(BaseCommand):
    help = (
        'Imports program application deadlines and admission '
        'information from a Slate instance.'
    )

    programs = []
    programs_count = 0
    programs_matched = set()
    default_deadline_data = []
    deadline_data = []
    rows_skipped_count = 0
    deadlines_matched_count = 0
    deadlines_skipped_count = 0
    deadlines_deleted_count = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--graduate',
            type=bool,
            help='''\
            Set to True if this is an import of graduate
            application deadline data
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

        # Fetch all application deadline data:
        self.get_default_deadline_data()
        self.get_deadline_data()

        # Assign deadline data to existing programs:
        self.assign_deadline_data()

        # Delete stale data:
        self.delete_stale_deadlines()

        # Print results
        self.print_results()

    def get_default_deadline_data(self):
        """
        Retrieves default application deadline data from
        local settings.
        """
        defaults = settings.PROGRAM_APPLICATION_DEADLINES

        for deadline_data in defaults:
            if deadline_data['career'] == self.career:
                self.default_deadline_data.append(deadline_data)

    def get_deadline_data(self):
        """
        Retrieves deadline data from an external Slate instance.
        """
        if self.career == 'Undergraduate':
            self.get_undergraduate_deadline_data()
        else:
            self.get_graduate_deadline_data()

    def get_undergraduate_deadline_data(self):
        """
        Retrieves and sets undergraduate deadline data.
        """
        # We don't have unique undergraduate deadline data
        # right now--add logic later if we get any.
        return

    def get_graduate_deadline_data(self):
        """
        Retrieves and sets graduate deadline data from
        Graduate Studies' Slate instance.
        """
        credentials = settings.GRADUATE_SLATE_ENDPOINTS['deadlines']

        try:
            response = requests.get(
                credentials['endpoint'],
                auth=(credentials['username'], credentials['password'])
            )
            response_str = response.text
            # Make their null values actually parse to `null` and not "NULL":
            response_str_cleaned = response_str.replace('"NULL"', 'null')
            response_json = json.loads(response_str_cleaned)
        except Exception, e:
            logging.warning(
                '\nError retrieving Graduate deadline data: {0}'
                .format(e)
            )
        else:
            self.deadline_data = response_json['row']

    def assign_deadline_data(self):
        """
        Handles creation and assignment of deadline data
        objects/field values by career type.
        """
        # If we have new deadline data to process, delete any existing data.
        # Otherwise, abort this process:
        if len(self.default_deadline_data) or len(self.deadline_data):
            print (
                (
                    'Deleting all existing application deadline data '
                    'for {0} Programs.'
                ).format(
                    self.career
                )
            )

            # Delete all ApplicationDeadlines by self.career
            ApplicationDeadline.objects.filter(career__name=self.career).delete()

            # Clear application_requirements on all programs in self.programs:
            if self.programs_count:
                self.programs.update(
                    application_requirements=None
                )
        else:
            print (
                'No deadline data to process. Creation and assignment of new '
                'program deadline data aborted.'
            )
            return

        # Ceate and assign default deadlines from
        # PROGRAM_APPLICATION_DEADLINES:
        self.assign_deadline_data_defaults()

        # Run career-specific deadline imports:
        if self.career == 'Undergraduate':
            self.assign_undergraduate_deadline_data()
        else:
            self.assign_graduate_deadline_data()

    def assign_deadline_data_defaults(self):
        """
        Handles creation and assignment of deadline data
        objects/field values from `self.default_deadline_data`.
        """
        for deadline_data in self.default_deadline_data:
            try:
                # Fetch career, levels:
                career = Career.objects.get(
                    name=deadline_data['career']
                )

                levels = []
                if deadline_data['level']:
                    levels = Level.objects.filter(
                        name__in=deadline_data['level']
                    )
            except Career.DoesNotExist:
                logging.warning(
                    (
                        'Cannot find existing Career {0}. '
                        'Skipping default deadline data row'
                    ).format(deadline_data['career'])
                )
                self.rows_skipped_count += 1
            except Career.MultipleObjectsReturned:
                logging.warning(
                    (
                        'Career {0} returned multiple objects. '
                        'Skipping default deadline data row'
                    ).format(deadline_data['career'])
                )
                self.rows_skipped_count += 1
            except Level.DoesNotExist:
                logging.warning(
                    (
                        'Cannot find existing Level {0}. '
                        'Skipping default deadline data row'
                    ).format(deadline_data['level'])
                )
                self.rows_skipped_count += 1
            else:
                # Fetch term and deadline type:
                term, term_created = AdmissionTerm.objects.get_or_create(
                    name=deadline_data['admission_term']
                )
                deadline_type, deadline_type_created = AdmissionDeadlineType.objects.get_or_create(
                    name=deadline_data['deadline_type']
                )

                try:
                    # Determine month + day from string
                    deadline_date = parse(deadline_data['display'])
                except ValueError:
                    logging.warning(
                        (
                            'Cannot determine month and day from '
                            'display string {0} in default deadline data. '
                            'Skipping default deadline data row'
                        ).format(deadline_data['display'])
                    )
                    self.rows_skipped_count += 1
                else:
                    # Create or retrieve an existing deadline
                    deadline, deadline_created = ApplicationDeadline.objects.get_or_create(
                        admission_term=term,
                        career=career,
                        deadline_type=deadline_type,
                        month=deadline_date.month,
                        day=deadline_date.day
                    )

                    # Assign deadline to programs by level(s)
                    programs = self.programs.filter(level=levels)
                    deadline.programs.add(*programs)

                    self.deadlines_matched_count += 1
                    self.programs_matched.update(programs)

    def assign_undergraduate_deadline_data(self):
        """
        Handles creation and assignment of deadline data
        objects/field values from `self.deadline_data` for
        Undergraduate Programs.
        """
        return

    def assign_graduate_deadline_data(self):
        """
        Handles creation and assignment of deadline data
        objects/field values from `self.deadline_data` for
        Graduate Programs.
        """
        career = Career.objects.get(name=self.career)
        term_spring, term_spring_created = AdmissionTerm.objects.get_or_create(
            name='Spring'
        )
        term_summer, term_summer_created = AdmissionTerm.objects.get_or_create(
            name='Summer'
        )
        term_fall, term_fall_created = AdmissionTerm.objects.get_or_create(
            name='Fall'
        )
        type_domestic, type_domestic_created = AdmissionDeadlineType.objects.get_or_create(
            name='Domestic'
        )
        type_international, type_international_created = AdmissionDeadlineType.objects.get_or_create(
            name='International'
        )

        for row in self.deadline_data:
            plan_code = row['Plan']
            subplan_code = row['SubPlan']
            program = None
            application_requirements = [r.strip() for r in row['ProgramApplicationRequirements'].split('|')] if row['ProgramApplicationRequirements'] else []
            deadlines = []

            # Make sure the program specified in this row of data
            # is valid before proceeding any further:
            try:
                program = Program.objects.get(
                    plan_code=plan_code,
                    subplan_code=subplan_code
                )
            except Program.DoesNotExist:
                logging.warning(
                    (
                        'Cannot find existing Program with plan '
                        'code "{0}" and subplan code "{1}" to '
                        'assign deadline data to. '
                        'Skipping deadline data row'
                    ).format(
                        plan_code,
                        subplan_code
                    )
                )
                self.rows_skipped_count += 1
            else:
                # Ensure existing deadline data is removed from the program
                # (e.g. that were added from default deadline data).
                # Deadline data being imported during this step takes
                # priority over default deadline data.
                program.application_deadlines.clear()

                # Determine which keys in the row of data contain
                # application deadline information by sniffing key names.
                # Assume that a key whose name contains "ApplicationDeadline"
                # has a value representing a single deadline.
                for key, val in row.items():
                    if 'ApplicationDeadline' in key and val:
                        admission_term = None
                        deadline_type = None

                        if key == 'SpringDomesticApplicationDeadline':
                            admission_term = term_spring
                            deadline_type = type_domestic
                        elif key == 'SummerDomesticApplicationDeadline':
                            admission_term = term_summer
                            deadline_type = type_domestic
                        elif key == 'FallDomesticApplicationDeadline':
                            admission_term = term_fall
                            deadline_type = type_domestic
                        elif key == 'SpringInternationalApplicationDeadline':
                            admission_term = term_spring
                            deadline_type = type_international
                        elif key == 'SummerInternationalApplicationDeadline':
                            admission_term = term_summer
                            deadline_type = type_international
                        elif key == 'FallInternationalApplicationDeadline':
                            admission_term = term_fall
                            deadline_type = type_international

                        if admission_term and deadline_type:
                            try:
                                # Determine month + day from string
                                deadline_date = parse(val)
                            except ValueError:
                                logging.warning(
                                    (
                                        'Cannot determine month and day from '
                                        'display string {0} in deadline data. '
                                        'Skipping deadline.'
                                    ).format(val)
                                )
                                self.deadlines_skipped_count += 1
                            else:
                                deadline, deadline_created = ApplicationDeadline.objects.get_or_create(
                                    admission_term=admission_term,
                                    career=career,
                                    deadline_type=deadline_type,
                                    month=deadline_date.month,
                                    day=deadline_date.day
                                )

                                program.application_deadlines.add(deadline)
                                program.application_requirements = application_requirements
                                program.save()

                                self.deadlines_matched_count += 1
                                self.programs_matched.add(program)
                                logging.info(
                                    (
                                        'Assigned deadline "{0}" to program "{1}" '
                                        '(plan code "{2}", subplan code "{3}")'
                                    ).format(
                                        deadline,
                                        program.name,
                                        program.plan_code,
                                        program.subplan_code
                                    )
                                )
                        else:
                            logging.warning(
                                (
                                    'Unknown deadline field {0}. '
                                    'Skipping deadline.'
                                ).format(key)
                            )
                            self.deadlines_skipped_count += 1

    def delete_stale_deadlines(self):
        """
        Deletes any deadlines (by career) not assigned to at least one program.
        """
        deadlines = ApplicationDeadline.objects.filter(
            career__name=self.career,
            programs=None
        )
        self.deadlines_deleted_count = deadlines.count()
        deadlines.delete()

    def print_results(self):
        print (
            'Finished import of {0} Program deadline data.'
        ).format(self.career)

        print (
            'Created one or more ApplicationDeadlines for {0}/{1} '
            'existing {2} Programs: {3: .0f} %'
        ).format(
            len(self.programs_matched),
            self.programs_count,
            self.career,
            float(len(self.programs_matched)) / float(self.programs_count) * 100
        )

        print (
            'Skipped {0} rows of deadline data.'
        ).format(
            self.rows_skipped_count
        )

        print (
            'Skipped {0} individual deadlines.'
        ).format(
            self.deadlines_skipped_count
        )

        print (
            'Deleted {0} Deadlines with no assigned Programs.'
        ).format(
            self.deadlines_deleted_count
        )
