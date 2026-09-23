from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.testing import SmokeTestCase
from programs.models import Career, Degree, Level, Program


JOBS_PAGE = b'''
<div class="job-search-results-card-title">
    <a href="https://jobs.ucf.edu/jobs/12345">Web Developer</a>
</div>
'''


class CoreSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.program = Program.objects.create(
            name='Biology',
            plan_code='BIOL-BS',
            level=Level.objects.create(name='Bachelors'),
            career=Career.objects.create(name='Undergraduate'),
            degree=Degree.objects.create(name='BS'),
        )

    def setUp(self):
        cache.clear()

    def test_home_page(self):
        self.assertGetOK(reverse('home'))

    def test_dashboard_pages(self):
        self.client.force_login(self.superuser)
        self.assertEndpointsOK([
            'dashboard',
            'dashboard.usage',
            'dashboard.programs.list',
            ('dashboard.programs.edit', {'pk': self.program.pk}),
        ])

    def test_open_positions(self):
        # The view scrapes jobs.ucf.edu, so the request is mocked.
        with mock.patch('core.views.requests.get') as get:
            get.return_value.content = JOBS_PAGE
            response = self.assertGetOK(reverse('api.positions.list'))

        self.assertEqual(response.json(), [
            {'title': 'Web Developer', 'externalPath': '/12345'},
        ])

    def test_admin_pages(self):
        for app_label in ['auth', 'authtoken', 'taggit', 'auditlog']:
            with self.subTest(app=app_label):
                self.assertAdminPagesOK(app_label)


class MigrationTests(TestCase):
    def test_no_missing_migrations(self):
        output = StringIO()
        try:
            call_command('makemigrations', '--check', '--dry-run', stdout=output)
        except SystemExit:
            self.fail(f'Models have changes without migrations:\n{output.getvalue()}')
