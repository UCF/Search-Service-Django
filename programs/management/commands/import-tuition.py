from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib
import urllib2
import json
import re

class Command(BaseCommand):
    help = 'Imports tuition data from Student Accounts'
    mappings = []
    fee_schedules = {}

    # Counts for results
    program_count = 0
    program_skipped = 0
    update_count = 0
    mapping_found = 0

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The url of the Student Accounts tuition feed')

    def handle(self, *args, **options):
        path = options['path']
        response = urllib2.urlopen(path)

        self.mappings = TuitionOverride.objects.all()

        # Set the fee_schedules to the array
        self.set_fee_schedules(path)

        # Set the data for each fee_schedule
        self.set_fee_data(path)

        # Update programs
        self.update_programs()

        # Print Results
        self.print_results()

    def set_fee_schedules(self, path):
        query = urllib.urlencode({
            'schoolYear': 'current',
            'feeName': 'Tuition'
        })

        request_url = '{0}?{1}'.format(path, query)

        response = urllib2.urlopen(request_url)

        schedules = json.loads(response.read())

        for schedule in schedules:
            if schedule['Program'] not in self.fee_schedules.keys():
                self.fee_schedules[schedule['Program']] = {
                    'code': schedule['Program'],
                    'type': schedule['FeeType'],
                    'res' : '',
                    'nonres' : ''
                }

    def set_fee_data(self, path):
        for schedule in self.fee_schedules:
            values = self.fee_schedules[schedule]

            query = urllib.urlencode({
                'schoolYear': 'current',
                'program'   : schedule,
                'feeType'   : values['type']
            })

            request_url = '{0}?{1}'.format(path, query)

            response = urllib2.urlopen(request_url)

            data = json.loads(response.read())

            if len(data) == 0:
                continue

            resident = 0
            nonresident = 0

            for fee in data:
                if self.is_required_fee(fee):
                    resident += fee['MaxResidentFee']
                    nonresident += fee['MaxNonResidentFee']

            self.fee_schedules[schedule]['res'] = resident
            self.fee_schedules[schedule]['nonres'] = nonresident


    def is_required_fee(self, fee):
        # Create variable for easy access
        fee_name = fee['FeeName']

        # Find a mapping if there is one
        try:
            mapping = self.mappings.get(tuition_code=fee['Program'])
        except:
            mapping = None

        # Check mappings
        if mapping:
            for ex in mapping.required_fees.all():
                if ex.fee_name in fee_name:
                    return True

        # Get rid of Other Fees on in the exceptions
        return '(Per Hour)' not in fee_name and '(Per Term)' not in fee_name and '(Annual)' not in fee_name

    def update_programs(self):
        programs = Program.objects.all()
        self.program_count = programs.count()

        for program in programs:
            # Check for skip override
            try:
                mapping = self.mappings.get(plan_code=program.plan_code, subplan_code=program.subplan_code)
            except:
                mapping = None

            # Empty values if skip is true then continue
            if mapping and mapping.skip:
                program.resident_tuition = None
                program.nonresident_tuition = None
                program.tuition_type = None
                program.save()
                self.program_skipped += 1
                continue

            schedule_code = self.get_schedule_code(program, mapping)

            # If the schedule code is not found, skip
            if schedule_code is None:
                self.program_skipped += 1
                continue

            if self.fee_schedules.has_key(schedule_code):
                values = self.fee_schedules[schedule_code]
                program.resident_tuition = values['res']
                program.nonresident_tuition = values['nonres']
                program.tuition_type = values['type']
                self.update_count += 1
                program.save()


    def get_schedule_code(self, program, mapping):
        if mapping:
            self.mapping_found += 1
            return mapping.tuition_code

        if program.online:
            if program.level.name == 'Bachelors':
                return 'UOU'
            elif program.level.name in ['Masters', 'Doctoral']:
                return 'UOG'
        elif program.level.name in ['Bachelors', 'Minor']:
            return 'UnderGrad'
        elif program.level.name in ['Masters', 'Doctoral']:
            return 'Grad'

        return None

    def print_results(self):
        success_perc_number = float(self.update_count) / float(self.program_count) * 100
        success_perc_str = str(round(success_perc_number, 2))

        print """
Successfully update tuition data.
Updated    : {0}
Exceptions : {1}
Skipped    : {2}
Success %  : {3}%
        """.format(
            self.update_count,
            self.mapping_found,
            self.program_skipped,
            success_perc_str
        )
