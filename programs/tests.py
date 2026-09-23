from django.conf import settings
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

    def test_admin_pages(self):
        self.assertAdminPagesOK('programs')
