from core.testing import SmokeTestCase
from locations.models import Location


class LocationsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.location = Location.objects.create(name='Millican Hall')

    def test_list_endpoints(self):
        self.assertEndpointsOK(['api.locations.list'])

    def test_detail_endpoints(self):
        self.assertEndpointsOK([
            ('api.locations.detail', {'pk': self.location.pk}),
        ])

    def test_admin_pages(self):
        self.assertAdminPagesOK('locations')
