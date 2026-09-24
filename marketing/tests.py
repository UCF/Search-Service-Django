from core.testing import SmokeTestCase
from marketing.models import Quote


class MarketingSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.quote = Quote.objects.create(quote_text='Reach for the stars.')
        cls.quote.tags.add('Research', 'Alumni')

    def test_list_endpoints(self):
        self.assertEndpointsOK(['api.marketing.quotes.list'])

    def test_detail_endpoints(self):
        self.assertEndpointsOK([
            ('api.marketing.quotes.single', {'id': self.quote.pk}),
        ])

    def test_tag_filter(self):
        # Tags match regardless of case, and a quote matching several
        # requested tags comes back once.
        self.assertResultCount('api.marketing.quotes.list', {'tags': 'research'}, 1)
        self.assertResultCount('api.marketing.quotes.list', {'tags': 'RESEARCH, alumni'}, 1)
        self.assertResultCount('api.marketing.quotes.list', {'tags': 'athletics'}, 0)

    def test_admin_pages(self):
        self.assertAdminPagesOK('marketing')
