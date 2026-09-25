import csv
import os
import tempfile
from importlib import import_module
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from core.testing import SmokeTestCase
from programs.models import College, Department
from units.models import Employee, JobTitle, Unit


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


class ImportUnitsTests(TestCase):
    def import_csv(self, rows):
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, newline='') as f:
            csv.writer(f).writerows(rows)
        self.addCleanup(os.remove, f.name)
        call_command('import-units', f.name, stdout=StringIO())

    def test_reuses_existing_job_title_even_when_duplicated(self):
        # ext_job_id isn't unique, so a match can return several rows.
        # The import should reuse one, not add another.
        first = JobTitle.objects.create(ext_job_id='J100', ext_job_name='Web Developer')
        JobTitle.objects.create(ext_job_id='J100', ext_job_name='Web Developer')

        self.import_csv([[
            '0000001', 'Ada Lovelace', 'Ada', 'Lovelace', '',
            'D100', 'Biology', 'O100', 'Academic Affairs',
            'Academic Affairs', 'College of Sciences',
            'j100', 'Web Developer',
        ]])

        self.assertEqual(JobTitle.objects.count(), 2)
        self.assertEqual(
            list(Employee.objects.get(ext_employee_id='0000001').job_titles.all()),
            [first],
        )
