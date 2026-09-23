"""
Shared helpers for the smoke tests in each app's tests.py.

Smoke tests check that pages and endpoints respond without errors.
They are not behavior tests; they give every upgrade a baseline
to check against.
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse


class SmokeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            'smoke-admin',
            'smoke-admin@example.com',
            'smoke-password'
        )

    def assertGetOK(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response

    def assertEndpointsOK(self, endpoints):
        """
        GETs each endpoint and checks for a 200. Each item is a URL
        name, or a (URL name, kwargs) tuple.
        """
        for endpoint in endpoints:
            name, kwargs = endpoint if isinstance(endpoint, tuple) else (endpoint, None)
            with self.subTest(endpoint=name):
                self.assertGetOK(reverse(name, kwargs=kwargs))

    def assertAdminPagesOK(self, app_label):
        """
        Loads the changelist and add form for every model the app
        registers with the admin, and the change form for the first
        row of each model that has one. Read-only admins, which don't
        allow adding, skip the add form.
        """
        self.client.force_login(self.superuser)
        request = RequestFactory().get('/')
        request.user = self.superuser

        models = [m for m in admin.site._registry if m._meta.app_label == app_label]
        self.assertTrue(models, f'No models registered in the admin for {app_label}')

        for model in models:
            prefix = f'admin:{app_label}_{model._meta.model_name}'
            with self.subTest(model=model.__name__):
                self.assertGetOK(reverse(f'{prefix}_changelist'))

                if admin.site._registry[model].has_add_permission(request):
                    self.assertGetOK(reverse(f'{prefix}_add'))

                obj = model.objects.first()
                if obj:
                    self.assertGetOK(reverse(f'{prefix}_change', args=(obj.pk,)))
