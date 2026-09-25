from core.testing import SmokeTestCase
from locations.models import Location


class LocationsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.location = Location.objects.create(
            name='Millican Hall',
            object_type='Building',
            data_source='Campus Map',
        )

    def test_list_endpoints(self):
        self.assertEndpointsOK(['api.locations.list'])

    def test_detail_endpoints(self):
        self.assertEndpointsOK([
            ('api.locations.detail', {'pk': self.location.pk}),
        ])

    def test_text_filters(self):
        self.assertResultCount('api.locations.list', {'object_type': 'building'}, 1)
        self.assertResultCount('api.locations.list', {'object_type': 'parking'}, 0)
        self.assertResultCount('api.locations.list', {'data_source': 'CAMPUS MAP'}, 1)
        self.assertResultCount('api.locations.list', {'data_source': 'facilities'}, 0)

    def test_admin_pages(self):
        self.assertAdminPagesOK('locations')
