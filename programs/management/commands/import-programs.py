from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from programs.models import *

import requests
from auditlog.context import set_actor
import re
from tabulate import tabulate

from unidecode import unidecode


class Command(BaseCommand):
    help = 'Imports programs from the Academic Programs Inventory Master.'
    career_mappings = {
        "UGRD": "Undergraduate",
        "GRAD": "Graduate",
        "PROF": "Professional"
    }
    mappings = {}
    use_internal_mapping = False
    new_modified_date = None
    list_inactive = True
    programs_skipped = 0
    programs_processed = 0
    programs_added = 0
    programs_revalidated = 0
    programs_invalidated = 0
    programs_gained_locations = 0
    programs_lost_locations = 0
    programs_updated = 0
    colleges_added = 0
    departments_added = 0
    # Refers to colleges being removed from a program
    colleges_changed = 0
    # Refers to departments being removed from a program
    departments_changed = 0
    # A collection of program ids added or updated
    programs = []
    # A list of programs that were re-validated after previously being invalid
    revalidated_programs = []
    # A list of programs invalidated
    invalidated_programs = []
    # A list of programs that gained locations after previously having no active locations
    gained_locations_programs = []
    # A list of programs that had active locations set previously, but lost them
    lost_locations_programs = []
    # A list of inactive programs found in APIM data
    inactive_programs = []

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The url of the APIM API.')

        parser.add_argument(
            '--mapping-path',
            type=str,
            dest='mapping_path',
            help='The url of the mapping file.',
            required=False
        )

        parser.add_argument(
            '--use-internal-mapping',
            type=bool,
            dest='use_internal_mapping',
            help='Will use the college mappings within the search service data.',
            required=False
        )

        parser.add_argument(
            '--list-inactive',
            type=bool,
            dest='list_inactive',
            help='Will list inactive programs that were present in APIM data.',
            default=True,
            required=False
        )

        parser.add_argument(
            '--cip-version',
            type=str,
            dest='cip_version',
            help='The version of CIPs used by programs in this import.',
            default=settings.CIP_CURRENT_VERSION,
            required=False
        )

    def handle(self, *args, **options):
        self.new_modified_date = timezone.now()
        path = options['path']
        mapping_path = options['mapping_path']
        self.use_internal_mapping = options['use_internal_mapping']
        self.list_inactive = options['list_inactive']
        self.cip_version = options['cip_version']
        response = requests.get(path)
        self.actor_id = getattr(settings, 'IMPORT_USER_ID', 1)

        if mapping_path and not self.use_internal_mapping:
            mapping_resp = requests.get(mapping_path)
            self.mappings = mapping_resp.json()
        elif self.use_internal_mapping:
            self.mappings = CollegeOverride.objects.all()
        else:
            self.mappings = None

        with set_actor(self.actor_id):
            data = response.json()

            # Create/update programs from feed data
            for d in data:
                if self.program_is_valid(d):
                    program = self.add_program(d)

                    if len(d['SubPlans']) > 0:
                        for sp in d['SubPlans']:
                            if self.subplan_is_valid(sp):
                                self.add_subplan(sp, program)
                            else:
                                self.programs_skipped += 1
                else:
                    self.programs_skipped += 1

            self.invalidate_stale_programs()
            self.__create_import_record()
            self.print_results()

            return 0

    def __create_import_record(self):
        """
        Creates a record of the import and stats
        for use in the Communicator Dashboard
        """
        try:
            record = ProgramImportRecord.objects.create(
                start_date_time = self.new_modified_date,
                end_date_time = timezone.now(),
                programs_processed = self.programs_processed,
            )

            record.save()

            record.programs_created.set(Program.objects.filter(
                created__gte=self.new_modified_date
            ))

            record.programs_modified.set(Program.objects.filter(
                created__lt=self.new_modified_date,
                modified__gte=self.new_modified_date
            ))

            record.programs_invalidated.set(self.invalidated_programs)
            record.programs_revalidated.set(self.revalidated_programs)

            self.stdout.write(self.style.SUCCESS("Successfully wrote import record!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f"There was an error writing the Import Record: {e}"
            ))


    def program_is_valid(self, data):
        """
        Returns whether or not APIM data representing a
        top-level program plan is considered valid.
        """
        # Ignore pending and non-degree programs
        if data['Meta Data'][0]['Degree'] in ['PND', 'PRP']:
            return False

        # Ensure other required values are not empty
        required = [
            data['College_Full'],
            data['Plan'],
            data['PlanName'],
            data['Career'],
            data['Meta Data'][0]['Degree'],
            data['CollegeShort'],
            data['Dept_Full']
        ]
        for val in required:
            if not val:
                return False

        return True

    def subplan_is_valid(self, data):
        """
        Returns whether or not APIM data representing a
        subplan is considered valid.
        """
        required = [
            data['Subplan'],
            data['Subplan_Name'],
            data['Meta Data'][0]['Degree']
        ]
        for val in required:
            if not val:
                return False

        return True

    def program_has_locations(self, data):
        """
        Returns whether or not the program is offered at
        at least one active location/campus.

        Only Bachelors programs utilize the Active Locations
        value in APIM--so just return True for all other
        program types.
        """
        if (
            self.career_mappings[data['Career']] == 'Undergraduate'
            and data['Meta Data'][0]['Degree'] not in ['CER', 'CRT', 'MIN']
            and len(data['Active Locations']) == 0
        ):
            return False

        return True

    def subplan_has_locations(self, data, parent_program):
        """
        Returns whether or not the subplan is offered at
        at least one active location/campus.

        Only Bachelors programs utilize the Active Locations
        value in APIM--so just return True for all other
        program types.
        """
        parent_career = parent_program.career.name
        if parent_program.career.name == 'Undergraduate' and len(data['Active Locations']) == 0:
            return False

        return True

    def set_program_name(self, program) -> str:
        """
        Appends any additional information onto the program
        name based on its level.
        """
        retval = program.name
        if program.level.name == 'Minor' and 'Minor' not in program.name:
            retval = f"{program.name} Minor"
        elif program.level.name == 'Certificate' and f'{program.career.name} Certificate' not in program.name:
            retval = self.update_certificate_name(program.name, program.career.name)

        return retval


    def update_certificate_name(self, program_name, career_name) -> str:
        """
        Updates 'Certificate' to 'Undergraduate Certificate' or
        'Graduate Certificate' based on the program career name.
        """
        if program_name.rstrip()[-12:] == ' Certificate':
            return f"{program_name[:-12]} {career_name} Certificate"

        return program_name


    def add_program(self, data):
        program = None
        self.programs_processed += 1
        program_exists = False

        # Correct college name issue
        data['College_Full'] = self.common_replace(data['College_Full'])

        try:
            program = Program.objects.get(plan_code=data['Plan'], subplan_code__isnull=True)
            program.name = unidecode(data['PlanName'])
            self.programs_updated += 1
            program_exists = True
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['PlanName']),
                plan_code=data['Plan']
            )
            self.programs_added += 1

        # Ensure the program is marked as valid
        if not program.valid:
            program.valid = True
            self.revalidated_programs.append(program.pk)
            self.programs_revalidated += 1

        # If the program is inactive in our data,
        # note the inactive program for output
        if program.active == False and data['Meta Data'][0]['Status'] == 'A':
            self.inactive_programs.append(program.pk)

        # Handle "has_locations" flag
        has_locations = self.program_has_locations(data)
        if program_exists and program.has_locations == False and has_locations == True:
            self.gained_locations_programs.append(program.pk)
            self.programs_gained_locations += 1
        elif program_exists and program.has_locations == True and has_locations == False:
            self.lost_locations_programs.append(program.pk)
            self.programs_lost_locations += 1
        program.has_locations = has_locations

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

        if self.program_is_online(data):
            program.online = True

        program.name = self.set_program_name(program)

        program.save()

        self.programs.append(program.id)

        mapping = None

        if self.mappings:
            if self.use_internal_mapping:
                try:
                    mapping = self.mappings.filter(plan_code=data['Plan'], subplan_code=None)
                except:
                    mapping = None
            else:
                mapping = [x for x in self.mappings['programs'] if x['plan_code'] == data['Plan'] and x['subplan_code'] == None]

        if mapping:
            if self.use_internal_mapping:
                mapping = mapping[0]
                data['College_Full'] = mapping.college.full_name
                data['CollegeShort'] = mapping.college.short_name
            else:
                mapping = mapping[0]
                data['College_Full'] = mapping['college']['name']
                data['CollegeShort'] = mapping['college']['short_name']


        # Handle Colleges
        college, create = College.objects.get_or_create(
            full_name=data['College_Full'],
            short_name=data['CollegeShort']
        )

        program.colleges.add(college)

        college_removed = False

        # Remove non-primary colleges
        for c in program.colleges.all():
            if c.short_name != college.short_name:
                program.colleges.remove(c)
                if college_removed == False:
                    college_removed = True


        if college_removed:
            self.colleges_changed += 1

        # Handle Departments
        department, create = Department.objects.get_or_create(
            full_name=data['Dept_Full']
        )

        if "school" in department.full_name.lower():
            department.school = True
            department.save()

        program.departments.add(department)

        department_removed = False

        for d in program.departments.all():
            if d.full_name != department.full_name:
                program.departments.remove(d)
                if department_removed == False:
                    department_removed = True

        if department_removed:
            self.departments_changed += 1

        # Remove any existing relationship to a current-version CIP
        # if it exists (in case the CIP changed in this import
        # for some reason).
        existing_cips = program.cip.filter(version=self.cip_version)
        if existing_cips.exists():
            program.cip.remove(*existing_cips)

        # Add an existing, current-version CIP object to the program.
        if data['CIP']:
            try:
                cip = CIP.objects.get(version=self.cip_version, code=data['CIP'])
                program.cip.add(cip)
            except CIP.DoesNotExist:
                pass

        if data['Meta Data'][0]['TermStart'] is not None:
            term_start_full = data['Meta Data'][0]['TermStart'];
            academic_term = None

            try:
                academic_term = AcademicTerm.objects.get(full_name=term_start_full)
            except AcademicTerm.DoesNotExist:
                academic_term = AcademicTerm(full_name=term_start_full)
                academic_term.save()

            if academic_term is not None:
                program.start_term = academic_term


        program.modified = self.new_modified_date

        program.save()

        return program

    def add_subplan(self, data, parent):
        program = None
        self.programs_processed += 1
        program_exists = False

        try:
            program = Program.objects.get(
                plan_code=parent.plan_code,
                subplan_code=data['Subplan']
            )

            program.name = unidecode(data['Subplan_Name'])
            self.programs_updated += 1
            program_exists = True
        except Program.DoesNotExist:
            program = Program(
                name=unidecode(data['Subplan_Name']),
                plan_code=parent.plan_code,
                subplan_code=data['Subplan'],
                parent_program=parent
            )
            self.programs_added += 1

        # Ensure the program is marked as valid
        if not program.valid:
            program.valid = True
            self.revalidated_programs.append(program.pk)
            self.programs_revalidated += 1

        # If the program is inactive in our data,
        # note the inactive program for output
        if program.active == False and data['Meta Data'][0]['Status'] == 'A':
            self.inactive_programs.append(program.pk)

        has_locations = self.subplan_has_locations(data, parent)
        if program_exists and program.has_locations == False and has_locations == True:
            self.gained_locations_programs.append(program.pk)
            self.programs_gained_locations += 1
        elif program_exists and program.has_locations == True and has_locations == False:
            self.lost_locations_programs.append(program.pk)
            self.programs_lost_locations += 1
        program.has_locations = has_locations

        # Handle Career and Level
        program.career = parent.career
        program.level = parent.level

        # Handle degree
        degree, created = Degree.objects.get_or_create(
            name=data['Meta Data'][0]['Degree']
        )

        program.degree = degree

        if self.program_is_online(data):
            program.online = True

        program.save()

        self.programs.append(program.id)

        # Handle CIP. Subplans should always use the
        # parent program's CIP(s)
        for cip in parent.cip.all():
            program.cip.add(cip)

        # Handle Colleges and Departments
        for college in parent.colleges.all():
            program.colleges.add(college)

        college_removed = False

        # Remove non-primary colleges
        for college in program.colleges.exclude(pk__in=parent.colleges.all().values_list('pk', flat=True)):
            program.colleges.remove(college)
            college_removed = True

        if college_removed:
            self.colleges_changed += 1

        for department in parent.departments.all():
            program.departments.add(department)

        department_removed = False

        # Remove non-primary departments
        for department in program.departments.exclude(pk__in=parent.departments.all().values_list('pk', flat=True)):
            program.departments.remove(department)
            department_removed = True

        if department_removed:
            self.departments_changed += 1

        if data['Meta Data'][0]['TermStart'] is not None:
            term_start_full = data['Meta Data'][0]['TermStart'];
            academic_term = None

            try:
                academic_term = AcademicTerm.objects.get(full_name=term_start_full)
            except AcademicTerm.DoesNotExist:
                academic_term = AcademicTerm(full_name=term_start_full)
                academic_term.save()

            if academic_term is not None:
                program.start_term = academic_term


        program.modified = self.new_modified_date

        program.save()

    def program_is_online(self, data):
        """
        Determines whether a program from APIM should
        be flagged as an online program.
        """
        # Check the actual "is online" flag from APIM
        if data['Meta Data'][0]['UCFOnline'] == "1":
            return True
        # Check subplan code for Z-code
        if 'Subplan' in data and data['Subplan'].startswith('Z'):
            return True

        online_regex = r"(\s)online(\s)?"

        # Check plan name for "online"
        if 'PlanName' in data and re.search(online_regex, data['PlanName'], re.IGNORECASE) is not None:
            return True
        # Check subplan name for "online"
        if 'Subplan_Name' in data and re.search(online_regex, data['Subplan_Name'], re.IGNORECASE) is not None:
            return True

        return False

    def common_replace(self, input):
        """
        Performs a general set of string replacements
        against a given input string.
        """
        input = input.replace('College of Business Administration', 'College of Business')
        input = input.replace('&', 'and')
        return input

    def invalidate_stale_programs(self):
        """
        Invalidate all programs not processed during the import
        """
        stale_programs = Program.objects.filter(
            valid=True,
            modified__lt=self.new_modified_date
        )

        for program in stale_programs:
            program.valid = False
            program.save()
            self.invalidated_programs.append(program.pk)

        self.programs_invalidated += stale_programs.count()

    def print_results(self):
        """
        Prints the results of the import to the stdout
        """
        results = [
            ('Programs Skipped', self.programs_skipped),
            ('Programs Processed', self.programs_processed),
            ('Programs Created', self.programs_added),
            ('Programs Updated', self.programs_updated),
            ('Programs Invalidated', self.programs_invalidated),
            ('Programs Revalidated', self.programs_revalidated),
            ('Programs that Gained Active Locations', self.programs_gained_locations),
            ('Programs that Lost Active Locations', self.programs_lost_locations)
        ]
        relationships = [
            ('Programs with college change', self.colleges_changed),
            ('Programs with department change', self.departments_changed),
        ]
        taxonomies = [
            ('Colleges Created', self.colleges_added),
            ('Departments Created', self.departments_added)
        ]

        self.stdout.write('''
Import Complete!

        ''')

        self.stdout.write(tabulate(results, tablefmt='grid'), ending='\n\n')
        self.stdout.write(tabulate(relationships, tablefmt='grid'), ending='\n\n')
        self.stdout.write(tabulate(taxonomies, tablefmt='grid'), ending='\n\n')

        if self.programs_invalidated > 0:
            self.stdout.write(
                (
                    '{0} programs were marked as invalid during this import:'
                ).format(self.programs_invalidated),
                ending='\n\n'
            )
            row_headers = ["Name", "Level", "Degree", "Career"]
            programs = Program.objects.filter(pk__in=self.invalidated_programs).values_list('name', 'level__name', 'degree__name', 'career__name')
            self.stdout.write(tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write("No programs were marked as invalid during this import.", ending='\n\n')

        if self.programs_revalidated > 0:
            self.stdout.write(
                (
                    '{0} programs previously marked as invalid were made '
                    'valid during this import:'
                ).format(self.programs_revalidated),
                ending='\n\n'
            )
            row_headers = ["Name", "Level", "Degree", "Career"]
            programs = Program.objects.filter(pk__in=self.revalidated_programs).values_list('name', 'level__name', 'degree__name', 'career__name')
            self.stdout.write(tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write("No existing invalid programs were marked as valid during this import.", ending='\n\n')

        if self.programs_gained_locations > 0:
            self.stdout.write(
                (
                    '{0} programs that previously had no active locations '
                    'gained locations during this import:'
                ).format(self.programs_gained_locations),
                ending='\n\n'
            )
            row_headers = ["Name", "Level", "Degree", "Career"]
            programs = Program.objects.filter(pk__in=self.gained_locations_programs).values_list(
                'name', 'level__name', 'degree__name', 'career__name')
            self.stdout.write(
                tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write(
                "No existing programs with zero active locations gained active locations during this import.", ending='\n\n')


        if self.programs_lost_locations > 0:
            self.stdout.write(
                (
                    '{0} programs that previously had active locations '
                    'lost their active locations during this import:'
                ).format(self.programs_lost_locations),
                ending='\n\n'
            )
            row_headers = ["Name", "Level", "Degree", "Career"]
            programs = Program.objects.filter(pk__in=self.lost_locations_programs).values_list(
                'name', 'level__name', 'degree__name', 'career__name')
            self.stdout.write(
                tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write(
                "No existing programs with active locations lost their active locations during this import.", ending='\n\n')

        if len(self.inactive_programs) > 0 and self.list_inactive:
            self.stdout.write("Inactive Programs Present in Source Data (" + str(len(self.inactive_programs)) + "):", ending='\n\n')
            row_headers = ["Name", "Level", "Degree", "Career", "PlanCode", "SubPlanCode"]
            programs = Program.objects.filter(pk__in=self.inactive_programs).values_list('name', 'level__name', 'degree__name', 'career__name', 'plan_code', 'subplan_code')
            self.stdout.write(tabulate(programs, headers=row_headers, tablefmt='grid'), ending='\n\n')
        else:
            self.stdout.write("There were no inactive programs found in the source data.", ending='\n\n')
