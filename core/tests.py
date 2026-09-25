from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.authtoken.models import Token

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

    def test_open_positions_cache_error(self):
        with mock.patch('core.views.requests.get') as get, \
                mock.patch('core.utils.jobs_utils.cache.set', side_effect=RuntimeError('cache down')):
            get.return_value.content = JOBS_PAGE
            with self.assertLogs(level='ERROR'):
                response = self.client.get(reverse('api.positions.list'))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['details'], 'cache down')

    def test_admin_pages(self):
        for app_label in ['auth', 'authtoken', 'taggit', 'auditlog']:
            with self.subTest(app=app_label):
                self.assertAdminPagesOK(app_label)


class HealthCheckTests(TestCase):
    def test_healthy(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
        self.assertIn('no-cache', response['Cache-Control'])

    def test_database_unavailable(self):
        with mock.patch('core.views.connection.cursor', side_effect=DatabaseError):
            with self.assertLogs(level='ERROR'):
                response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 503)


@override_settings(
    CACHE_CONTROL_ENABLED=True,
    CACHE_CONTROL_TTLS={
        '/': 0,
        '/api/v1/': 3600,
        '/api/v1/research/': 86400,
    }
)
class CacheControlTests(SmokeTestCase):
    def assertCacheControl(self, url, expected, **extra):
        response = self.client.get(url, **extra)
        self.assertEqual(response['Cache-Control'], expected, url)

    def test_anonymous_api(self):
        self.assertCacheControl('/api/v1/programs/', 'public, max-age=3600')

    def test_longest_prefix_wins(self):
        self.assertCacheControl('/api/v1/research/researchers/', 'public, max-age=86400')

    def test_zero_ttl(self):
        self.assertCacheControl('/', 'private, no-store')

    def test_signed_in(self):
        self.client.force_login(self.superuser)
        self.assertCacheControl('/api/v1/programs/', 'private, no-store')

    def test_api_key(self):
        key = Token.objects.get(user=self.superuser).key
        self.assertCacheControl(f'/api/v1/programs/?key={key}', 'private, no-store')

    def test_not_found(self):
        self.assertCacheControl('/api/v1/programs/0/', 'private, no-store')

    def test_existing_header_kept(self):
        self.assertIn('no-cache', self.client.get('/healthz')['Cache-Control'])

    @override_settings(CACHE_CONTROL_ENABLED=False)
    def test_disabled(self):
        self.assertFalse(self.client.get('/api/v1/programs/').has_header('Cache-Control'))


class MigrationTests(TestCase):
    def test_no_missing_migrations(self):
        output = StringIO()
        try:
            call_command('makemigrations', '--check', '--dry-run', stdout=output)
        except SystemExit:
            self.fail(f'Models have changes without migrations:\n{output.getvalue()}')
