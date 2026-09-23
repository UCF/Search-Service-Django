from core.testing import SmokeTestCase
from marketing.models import Quote


class MarketingSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.quote = Quote.objects.create(quote_text='Reach for the stars.')

    def test_list_endpoints(self):
        self.assertEndpointsOK(['api.marketing.quotes.list'])

    def test_detail_endpoints(self):
        self.assertEndpointsOK([
            ('api.marketing.quotes.single', {'id': self.quote.pk}),
        ])

    def test_admin_pages(self):
        self.assertAdminPagesOK('marketing')
