import datetime

from core.testing import SmokeTestCase
from podcasts.models import PodcastCategory, PodcastEpisode, PodcastShow


class PodcastsSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.category = PodcastCategory.objects.create(
            title='Research',
            description='Conversations about research.',
            slug='research',
        )
        cls.show = PodcastShow.objects.create(
            title='Knights Talk',
            feed_url='https://example.com/feed.xml',
            description='A show about UCF.',
            owner='UCF',
            category=cls.category,
        )
        cls.episode = PodcastEpisode.objects.create(
            guid='episode-1',
            title='Episode 1',
            description='The first episode.',
            published_date=datetime.date(2026, 1, 1),
            duration=datetime.timedelta(minutes=30),
            audio_file='https://example.com/episode-1.mp3',
            episode_type='full',
            show=cls.show,
            category=cls.category,
        )

    def test_list_endpoints(self):
        self.assertEndpointsOK([
            'api.podcasts.list',
            'api.podcasts.episodelist',
            'api.podcasts.categories.list',
        ])

    def test_detail_endpoints(self):
        self.assertEndpointsOK([
            ('api.podcasts.detail', {'id': self.show.pk}),
            ('api.podcasts.details.episodelist', {'id': self.show.pk}),
            ('api.podcasts.episode.summary', {'id': self.episode.pk}),
            ('api.podcasts.categories.detail', {'slug': self.category.slug}),
        ])

    def test_admin_pages(self):
        self.assertAdminPagesOK('podcasts')
