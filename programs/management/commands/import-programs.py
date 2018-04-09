from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2, json

class Command(BaseCommand):
    help = 'Imports programs from the Academic Programs Inventory Master.'
    career_mappings = {
        "UGRD": "Undergraduate",
        "GRAD": "Graduate",
        "PROF": "Professional"
    }

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The url of the APIM API.')

    def handle(self, *args, **options):
        path = options['path']
        response = urllib2.urlopen(path)

        data = json.loads(response.read())

        for d in data:
            self.add_program(d)

        return 0

    def add_program(self, data):
        program = None

        try:
            program = Program.objects.get(plan_code=data['Plan'])
        except Program.DoesNotExist:
            program = Program(name=data['PlanName'], plan_code=data['Plan'])

        # Handle Career
        career = self.career_mappings[data['Career']]
        career, created = Career.objects.get_or_create(name=career, abbr=data['Career'])

        program.career = career

        # Handle level
        if data['Level'] == '':
            data['Level'] = 'None'
        level, created = Level.objects.get_or_create(name=data['Level'])

        program.level = level

        # Handle degree
        degree, created = Degree.objects.get_or_create(name=data['Meta Data'][0]['Degree'])

        program.degree = degree

        program.save()
