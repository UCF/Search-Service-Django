from django.core.management.base import BaseCommand, CommandParser, CommandError
from programs.models import Program, JobPosition, WeightedJobPosition

import argparse
import csv
import mimetypes

class Command(BaseCommand):
    help = 'Imports the generated weighed jobs'

    fieldnames = [
        'program_id',
        'career',
        'weight'
    ]

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'file',
            type=argparse.FileType('r'),
            help='The file path of the csv file'
        )

    def handle(self, *args, **options):
        self.programs = {}
        self.file = options['file']

        mime_type, _ = mimetypes.guess_type(self.file.name)

        if mime_type != 'text/csv':
            raise CommandError('File provided is not a CSV file')

        # Remove existing records
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
        program_id = weighted_job['program_id']
        career_name = weighted_job['career']
        weight = weighted_job['weight']

        program = None
        job = None

        try:
            program = Program.objects.get(id=program_id)
        except Program.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Program with id {program_id} does not exist."))

        try:
            job = JobPosition.objects.get(name=career_name)
        except JobPosition.DoesNotExist:
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
