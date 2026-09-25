from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.authtoken.models import Token

from core.management.purge import PurgeAfterImportMixin
from core.testing import SmokeTestCase
from core.utils import front_door
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


FRONT_DOOR = {
    'subscription_id': 'sub',
    'resource_group': 'rg',
    'profile': 'profile',
    'endpoint': 'endpoint',
    'domains': ['search.ucf.edu'],
    'identity_client_id': '',
}
IDENTITY_ENV = {'IDENTITY_ENDPOINT': 'http://identity.local/token', 'IDENTITY_HEADER': 'secret'}


@override_settings(FRONT_DOOR=FRONT_DOOR)
@mock.patch.dict('os.environ', IDENTITY_ENV)
@mock.patch('core.utils.front_door.requests')
class FrontDoorPurgeTests(TestCase):
    def respond(self, requests, purge_status=202):
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = {'access_token': 'token'}
        requests.post.return_value.status_code = purge_status

    def test_purge(self, requests):
        self.respond(requests)
        self.assertTrue(front_door.purge(['/api/v1/research/*']))

        requests.get.assert_called_once_with(
            'http://identity.local/token',
            params={'resource': 'https://management.azure.com/', 'api-version': '2019-08-01'},
            headers={'X-IDENTITY-HEADER': 'secret'},
            timeout=30
        )
        requests.post.assert_called_once_with(
            'https://management.azure.com/subscriptions/sub/resourceGroups/rg'
            '/providers/Microsoft.Cdn/profiles/profile/afdEndpoints/endpoint/purge',
            params={'api-version': '2025-04-15'},
            headers={'Authorization': 'Bearer token'},
            json={'contentPaths': ['/api/v1/research/*'], 'domains': ['search.ucf.edu']},
            timeout=30
        )

    def test_user_assigned_identity(self, requests):
        self.respond(requests)
        with override_settings(FRONT_DOOR={**FRONT_DOOR, 'identity_client_id': 'client'}):
            front_door.purge(['/api/v1/*'])
        self.assertEqual(requests.get.call_args.kwargs['params']['client_id'], 'client')

    def test_not_configured(self, requests):
        with override_settings(FRONT_DOOR=None):
            self.assertFalse(front_door.purge(['/api/v1/*']))
        requests.get.assert_not_called()
        requests.post.assert_not_called()

    def test_no_managed_identity(self, requests):
        with mock.patch.dict('os.environ', clear=True):
            with self.assertRaises(front_door.PurgeError):
                front_door.purge(['/api/v1/*'])

    def test_purge_rejected(self, requests):
        self.respond(requests, purge_status=403)
        with self.assertRaises(front_door.PurgeError):
            front_door.purge(['/api/v1/*'])

    def test_purge_cache_command(self, requests):
        self.respond(requests)
        output = StringIO()
        call_command('purge-cache', '/api/v1/podcasts/*', stdout=output)
        self.assertEqual(requests.post.call_args.kwargs['json']['contentPaths'], ['/api/v1/podcasts/*'])
        self.assertIn('Requested a Front Door purge', output.getvalue())

    def test_purge_cache_command_needs_absolute_paths(self, requests):
        with self.assertRaises(CommandError):
            call_command('purge-cache', 'api/v1/*')


class ImportCommand(PurgeAfterImportMixin, BaseCommand):
    purge_paths = ['/api/v1/research/*']

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', dest='dry_run')

    def handle(self, *args, **options):
        pass


@mock.patch('core.management.purge.purge', return_value=True)
class PurgeAfterImportTests(TestCase):
    def run_import(self, *args):
        call_command(ImportCommand(), *args, stdout=StringIO())

    def test_purges_by_default(self, purge):
        self.run_import()
        purge.assert_called_once_with(['/api/v1/research/*'])

    def test_no_purge(self, purge):
        self.run_import('--no-purge')
        purge.assert_not_called()

    def test_dry_run(self, purge):
        self.run_import('--dry-run')
        purge.assert_not_called()

    def test_purge_failure(self, purge):
        purge.side_effect = front_door.PurgeError('denied')
        with self.assertRaisesMessage(CommandError, 'The import finished, but the Front Door purge failed'):
            self.run_import()

    def test_imports_have_the_flag(self, purge):
        from django.core.management import load_command_class
        for app, name in [
            ('programs', 'import-programs'),
            ('units', 'import-units'),
            ('research', 'acad-analytics-import-researchers'),
            ('podcasts', 'update-episodes'),
            ('locations', 'import_location_images'),
        ]:
            with self.subTest(command=name):
                self.assertIsInstance(load_command_class(app, name), PurgeAfterImportMixin)


class MigrationTests(TestCase):
    def test_no_missing_migrations(self):
        output = StringIO()
        try:
            call_command('makemigrations', '--check', '--dry-run', stdout=output)
        except SystemExit:
            self.fail(f'Models have changes without migrations:\n{output.getvalue()}')
