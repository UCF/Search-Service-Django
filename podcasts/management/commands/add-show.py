from django.core.management.base import BaseCommand

from podcasts.models import PodcastShow

class Command(BaseCommand):
    help = 'Adds a show from the podcast RSS feed'

    def add_arguments(self, parser):
        parser.add_argument(
            'rss_feed_url',
            type=str,
            help='The Podcast RSS to add to the database'
        )

    def handle(self, *args, **options):
        rss_feed_url = options['rss_feed_url']
        show = None
        try:
            show = PodcastShow.manager.add_show_from_rss(rss_feed_url)
        except:
            self.stderr.write(
                self.style.ERROR(f"Successfully added show: {show.title}")
            )

        if show is not None:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully added show: {show.title}")
            )

