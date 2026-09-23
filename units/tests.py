from core.testing import SmokeTestCase
from units.models import Unit


class UnitsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        parent = Unit.objects.create(name='College of Sciences')
        Unit.objects.create(name='Department of Biology', parent_unit=parent)

    def test_admin_pages(self):
        self.assertAdminPagesOK('units')
