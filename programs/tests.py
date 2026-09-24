from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from core.testing import SmokeTestCase
from programs.models import (
    CIP,
    Career,
    College,
    CollegeOverride,
    Degree,
    Department,
    JobPosition,
    Level,
    Program,
    ProgramDescription,
    ProgramDescriptionType,
    ProgramProfile,
    ProgramProfileType,
    TuitionOverride,
)


class ProgramsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        college = College.objects.create(full_name='College of Sciences')
        department = Department.objects.create(full_name='Department of Biology')
        cip = CIP.objects.create(name='Biology', description='Biology, general.', code='26.0101')
        job = JobPosition.objects.create(name='Biologist')

        cls.program = Program.objects.create(
            name='Biology',
            plan_code='BIOL-BS',
            level=Level.objects.create(name='Bachelors'),
            career=Career.objects.create(name='Undergraduate'),
            degree=Degree.objects.create(name='BS'),
            application_requirements=['Transcripts', 'Letters of recommendation'],
        )
        cls.program.colleges.add(college)
        cls.program.departments.add(department)
        cls.program.cip.add(cip)
        cls.program.jobs.add(job)

        # Program serializers look up the excerpt source by name, and
        # production always has this row.
        cls.description = ProgramDescription.objects.create(
            description_type=ProgramDescriptionType.objects.create(name=settings.EXCERPT_DESCRIPTION_TYPE_SOURCE),
            description='The study of living things.',
            program=cls.program,
        )
        cls.profile = ProgramProfile.objects.create(
            profile_type=ProgramProfileType.objects.create(name='Main Site', root_url='https://www.ucf.edu/'),
            url='https://www.ucf.edu/degree/biology-bs/',
            program=cls.program,
        )
        cls.tuition_override = TuitionOverride.objects.create(tuition_code='UGRD', plan_code='BIOL-BS')
        CollegeOverride.objects.create(plan_code='BIOL-BS', college=college)

        cls.college = college
        cls.department = department
        cls.cip = cip

    def test_list_endpoints(self):
        self.assertEndpointsOK([
            'api.core',
            'api.programs.list',
            'api.programs.search',
            'api.colleges.list',
            'api.colleges.search',
            'api.departments.list',
            'api.departments.search',
            'api.descriptions.types.list',
            'api.profiles.types.list',
            'api.collegeoverride.list',
            'api.tuitionoverride.list',
            'api.cip.list',
            'api.jobs.list',
        ])

    def test_detail_endpoints(self):
        program = {'id': self.program.pk}
        self.assertEndpointsOK([
            ('api.programs.detail', program),
            ('api.programs.outcomes', program),
            ('api.programs.projections', program),
            ('api.programs.careers', program),
            ('api.programs.careers.ranked', program),
            ('api.programs.deadlines', program),
            ('api.colleges.detail', {'id': self.college.pk}),
            ('api.departments.detail', {'id': self.department.pk}),
            ('api.descriptions.detail', {'id': self.description.pk}),
            ('api.profiles.detail', {'id': self.profile.pk}),
            ('api.tuitionoverride.detail', {'id': self.tuition_override.pk}),
            ('api.cip.detail.default_year', {'code': self.cip.code}),
        ])

    def test_search_filters_results(self):
        # Guards against filters silently switching off, which a
        # django-filter upgrade can do to views that set `filter_class`.
        url = reverse('api.programs.search')

        found = self.client.get(url, {'search': 'biol'}).json()
        missing = self.client.get(url, {'search': 'chemistry'}).json()

        self.assertEqual(found['count'], 1)
        self.assertEqual(missing['count'], 0)

    def test_application_requirements_are_a_list(self):
        url = reverse('api.programs.deadlines', kwargs={'id': self.program.pk})

        response = self.client.get(url).json()

        self.assertEqual(
            response['application_requirements'],
            ['Transcripts', 'Letters of recommendation'],
        )

    def test_admin_pages(self):
        self.assertAdminPagesOK('programs')


class ApplicationRequirementsMigrationTests(TransactionTestCase):
    """
    Migration 0068 moves application_requirements from django-mysql's
    comma-separated text to JSON. Production has real values, so this
    saves some through the old field and checks they come through.
    """
    before = [('programs', '0067_generate_college_department_slugs')]
    after = [('programs', '0068_application_requirements_json')]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        executor.loader.build_graph()
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        call_command('migrate', verbosity=0)

    def test_requirements_survive_the_move_to_json(self):
        old_apps = self.migrate(self.before)
        Program = old_apps.get_model('programs', 'Program')
        program_fields = {
            'level': old_apps.get_model('programs', 'Level').objects.create(name='Bachelors'),
            'career': old_apps.get_model('programs', 'Career').objects.create(name='Undergraduate'),
            'degree': old_apps.get_model('programs', 'Degree').objects.create(name='BS'),
        }
        with_list = Program.objects.create(
            name='Biology', plan_code='BIOL-BS',
            application_requirements=['Transcripts', 'Letters of recommendation'],
            **program_fields
        )
        with_empty_list = Program.objects.create(
            name='Chemistry', plan_code='CHEM-BS', application_requirements=[], **program_fields
        )
        with_none = Program.objects.create(
            name='Physics', plan_code='PHYS-BS', application_requirements=None, **program_fields
        )

        new_apps = self.migrate(self.after)
        Program = new_apps.get_model('programs', 'Program')

        self.assertEqual(
            Program.objects.get(pk=with_list.pk).application_requirements,
            ['Transcripts', 'Letters of recommendation'],
        )
        self.assertEqual(Program.objects.get(pk=with_empty_list.pk).application_requirements, [])
        self.assertIsNone(Program.objects.get(pk=with_none.pk).application_requirements)


class CaseInsensitiveLookupTests(TestCase):
    """
    MySQL compares text without regard to case and PostgreSQL doesn't.
    The imports and models match codes and names case-insensitively so
    they find the same rows on both.
    """
    @classmethod
    def setUpTestData(cls):
        cls.program = Program.objects.create(
            name='Biology',
            plan_code='BIOL-BS',
            level=Level.objects.create(name='Bachelors'),
            career=Career.objects.create(name='Undergraduate'),
            degree=Degree.objects.create(name='BS'),
        )
        cls.profile_type = ProgramProfileType.objects.create(name='Main Site', root_url='https://www.ucf.edu/')

    def test_profile_import_matches_regardless_of_case(self):
        response = mock.Mock(
            headers={'x-wp-totalpages': '1', 'x-wp-total': '1'},
            json=mock.Mock(return_value=[
                {'degree_meta': {'degree_code': 'biol-bs'}, 'link': 'https://www.ucf.edu/degree/biology-bs/'},
            ]),
        )
        with mock.patch('requests.get', return_value=response):
            call_command(
                'import-profiles',
                'https://www.ucf.edu/wp-json/wp/v2/degree',
                'main site',
                stdout=StringIO(),
                stderr=StringIO(),
            )

        profile = ProgramProfile.objects.get(program=self.program)
        self.assertEqual(profile.profile_type, self.profile_type)

    def test_tuition_override_finds_program_regardless_of_case(self):
        override = TuitionOverride.objects.create(tuition_code='UGRD', plan_code='biol-bs')

        self.assertEqual(override.program, self.program)
