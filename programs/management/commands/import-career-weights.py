from django.core.management.base import BaseCommand, CommandParser, CommandError
from programs.models import Program, JobPosition, WeightedJobPosition

import argparse
import csv
import mimetypes

class Command(BaseCommand):
    help = 'Imports the generated weighed jobs'

    program_fieldnames = [
        'program_id',
        'career',
        'weight'
    ]

    code_fieldnames = [
        'plan_code',
        'subplan_code',
        'career'
    ]

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'file',
            type=argparse.FileType('r'),
            help='The file path of the csv file'
        )

        parser.add_argument(
            '--code-fields',
            type=bool,
            dest='code_fields',
            help='Flag indicating the CSV provided uses the fields plan_code, subplan_code and career.',
            default=False
        )

        parser.add_argument(
            '--force-weight',
            type=float,
            dest='force_weight',
            help='When provided, will set all career weights to the value provided.',
            default=None,
            required=False
        )

        parser.add_argument(
            '--keep-existing',
            action='store_true',
            dest='keep_existing',
            default=False,
            help='When present, weight job positions will not be deleted prior to import',
        )

    def handle(self, *args, **options):
        self.programs = {}
        self.file = options['file']
        self.using_codefields = options['code_fields']
        self.fieldnames = self.code_fieldnames if self.using_codefields == True else self.program_fieldnames
        self.force_weight = float(options['force_weight']) if options['force_weight'] is not None else None
        self.keep_existing = options['keep_existing']

        mime_type, _ = mimetypes.guess_type(self.file.name)

        if mime_type != 'text/csv':
            raise CommandError('File provided is not a CSV file')

        # Remove existing records
        if not self.keep_existing:
            self.__remove_existing_data()

        # Import new data
        self.__import_data(self.file)


    def __remove_existing_data(self):
        WeightedJobPosition.objects.all().delete()

    def __import_data(self, csv_file):
        try:
            csv_reader = csv.DictReader(csv_file, fieldnames=self.fieldnames)
            # Skip the first row
            csv_reader.__next__()
        except csv.Error:
            raise CommandError('CSV does not have valid headers or is malformed.')

        for row in csv_reader:
            self.__add_weighted_job(row)


    def __add_weighted_job(self, weighted_job):
        if not self.using_codefields:
            program_id = weighted_job['program_id']
        else:
            plan_code = weighted_job['plan_code']
            subplan_code = weighted_job['subplan_code'] if weighted_job['subplan_code'] != '' else None

        career_name = weighted_job['career']
        weight = self.force_weight if self.force_weight is not None else weighted_job['weight']

        program = None
        job = None

        try:
            if not self.using_codefields:
                program = Program.objects.get(id=program_id)
            else:
                program = Program.objects.get(plan_code=plan_code, subplan_code=subplan_code)
                
        except Program.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Program with id {program_id} does not exist."))

        try:
            job = JobPosition.objects.get(name=career_name)
        except JobPosition.DoesNotExist:
            if self.using_codefields:
                job = JobPosition(name=career_name)
                job.save()
            else:
                self.stderr.write(self.style.ERROR(f"JobPosition with name {career_name} does not exist."))

        if program and job:
            try:
                existing = WeightedJobPosition.objects.get(program=program, job=job)
                existing.weight = weight
                existing.save()
            except WeightedJobPosition.DoesNotExist:
                new_wjp = WeightedJobPosition(
                    program=program,
                    job=job,
                    weight=weight
                )
                new_wjp.save()
