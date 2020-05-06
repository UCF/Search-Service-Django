from django.core.management.base import BaseCommand, CommandError
from programs.models import *

from dateutil.parser import *
import decimal
import itertools
import logging
import mimetypes
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
    deadlines_count = 0
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
        self.deadlines_count = len(self.default_deadline_data) + len(self.deadline_data)

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
        # TODO actually retrieve something
        self.deadline_data = []

    def assign_deadline_data(self):
        """
        Handles creation and assignment of deadline data
        objects/field values by career type.
        """
        # If we have new deadline data to process, delete any existing data.
        # Otherwise, abort this process:
        if self.deadlines_count:
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

            # Clear application_deadline_details and application_requirements
            # on all programs in self.programs:
            # TODO do we need to force a save on Program objects here?
            if self.programs.count():
                self.programs.update(
                    application_deadline_details=None,
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
                self.deadlines_skipped_count += 1
            except Career.MultipleObjectsReturned:
                logging.warning(
                    (
                        'Career {0} returned multiple objects. '
                        'Skipping default deadline data row'
                    ).format(deadline_data['career'])
                )
                self.deadlines_skipped_count += 1
            except Level.DoesNotExist:
                logging.warning(
                    (
                        'Cannot find existing Level {0}. '
                        'Skipping default deadline data row'
                    ).format(deadline_data['level'])
                )
                self.deadlines_skipped_count += 1
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
                    self.deadlines_skipped_count += 1
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
        for row in self.deadline_data:
            # TODO process and create/assign existing data

            # TODO implement an actual condition here
            if True:
                # TODO Remember to add matched programs to self.programs_matched!

                self.deadlines_matched_count += 1
                logging.info(unicode(
                    (
                        '\n MATCH Deadline data with TODO to {0} '
                        'existing programs'
                    ).format(
                        '0'  # TODO
                    )
                )).encode('ascii', 'xmlcharrefreplace')
            else:
                self.deadlines_skipped_count += 1
                logging.info(unicode(
                    (
                        '\n FAILURE Deadline data with TODO '
                        '- no program matches found'
                    ).format(
                        # TODO
                    )
                )).encode('ascii', 'xmlcharrefreplace')
        return

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

        if self.programs_count:
            print (
                'Created one or more ApplicationDeadlines for {0}/{1} '
                'existing {2} Programs: {3: .0f} %'
            ).format(
                len(self.programs_matched),
                self.programs_count,
                self.career,
                float(len(self.programs_matched)) / float(self.programs_count) * 100
            )

        if self.deadlines_count:
            print (
                'Matched {0}/{1} of fetched Deadline data rows to at least '
                'one existing {2} Program: {3:.0f}%'
            ).format(
                self.deadlines_matched_count,
                self.deadlines_count,
                self.career,
                float(self.deadlines_matched_count) / float(self.deadlines_count) * 100
            )

            print (
                'Skipped {0} rows of Deadline data.'
            ).format(
                self.deadlines_skipped_count
            )

            print (
                'Deleted {0} Deadlines with no assigned Programs.'
            ).format(
                self.deadlines_deleted_count
            )
