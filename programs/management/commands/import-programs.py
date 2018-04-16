from django.core.management.base import BaseCommand, CommandError
from programs.models import *

import urllib2
import json


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
            if d['Meta Data'][0]['Degree'] == 'PND':
                continue

            program = self.add_program(d)

            if len(d['SubPlans']) > 0:
                for sp in d['SubPlans']:
                    self.add_subplan(sp, program)

        return 0

    def add_program(self, data):
        program = None

        try:
            program = Program.objects.get(plan_code=data['Plan'])
        except Program.DoesNotExist:
            program = Program(name=data['PlanName'], plan_code=data['Plan'])

        # Handle Career
        career = self.career_mappings[data['Career']]
        career, created = Career.objects.get_or_create(
            name=career, abbr=data['Career']
        )

        program.career = career

        # Handle degree
        degree, created = Degree.objects.get_or_create(
            name=data['Meta Data'][0]['Degree']
        )

        program.degree = degree

        # Handle level
        temp_level = 'None'
        if data['Level'] == '':
            if degree.name in ['CER', 'CRT']:
                temp_level = 'Certificate'
            if degree.name == 'MIN':
                temp_level = 'Minor'
        else:
            temp_level = data['Level']

        level, created = Level.objects.get_or_create(name=temp_level)

        program.level = level

        if data['Meta Data'][0]['UCFOnline'] == "1":
            program.online = True

        program.save()

        # Handle Colleges
        college, create = College.objects.get_or_create(
            full_name=data['College_Full'],
            short_name=data['CollegeShort']
        )

        program.colleges.add(college)

        # Handle Departments
        department, create = Department.objects.get_or_create(
            full_name=data['Dept_Full']
        )

        if "school" in department.full_name.lower():
            department.school = True
            department.save()

        program.departments.add(department)

        program.save()

        return program

    def add_subplan(self, data, parent):
        program = None

        try:
            program = Program.objects.get(
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'])
        except Program.DoesNotExist:
            program = Program(
                name=data['Subplan_Name'],
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'],
                parent_program=parent
            )

        # Handle Career and Level

        program.career = parent.career
        program.level = parent.level

        # Handle degree
        degree, created = Degree.objects.get_or_create(
            name=data['Meta Data'][0]['Degree']
        )

        program.degree = degree

        if data['Meta Data'][0]['UCFOnline'] == "1":
            program.online = True

        program.save()

        # Handle Colleges and Departments
        for college in parent.colleges.all():
            program.colleges.add(college)

        for department in parent.departments.all():
            program.departments.add(department)

        program.save()
