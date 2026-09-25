from importlib import import_module
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from core.testing import SmokeTestCase
from programs.models import College, Department
from units.models import Unit


class UnitsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        parent = Unit.objects.create(name='College of Sciences')
        Unit.objects.create(name='Department of Biology', parent_unit=parent)

    def test_admin_pages(self):
        self.assertAdminPagesOK('units')


class MapUnitsTests(TestCase):
    def test_consolidates_duplicates_that_differ_only_in_case(self):
        # MySQL grouped unit names without regard to case, so these two
        # were always treated as duplicates. PostgreSQL has to do the same.
        def create_units(command):
            parent = Unit.objects.create(name='College of Sciences')
            Unit.objects.create(name='Department of Biology', parent_unit=parent)
            orphan = Unit.objects.create(name='DEPARTMENT OF BIOLOGY')
            Unit.objects.create(name='Biology Lab', parent_unit=orphan)

        # The command's closing stats divide by these counts.
        College.objects.create(full_name='College of Sciences')
        Department.objects.create(full_name='Department of Biology')

        command = import_module('units.management.commands.map-units').Command
        with mock.patch.object(command, 'map_orgs_colleges', autospec=True, side_effect=create_units), \
                mock.patch.object(command, 'map_depts_programs', autospec=True):
            call_command('map-units', stdout=StringIO(), stderr=StringIO())

        self.assertEqual(Unit.objects.filter(name__iexact='Department of Biology').count(), 1)
        self.assertEqual(
            Unit.objects.get(name='Biology Lab').parent_unit.name,
            'Department of Biology',
        )
