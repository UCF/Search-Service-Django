from django.core.management.base import BaseCommand
from django.core.files import File

from podcasts.models import PodcastShow

from typing import Optional, Tuple

import feedparser
import requests
import tempfile

class Command(BaseCommand):
    help = 'Updated show descriptions and images'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    }

    def handle(self, *args, **options):
        self.shows_processed = 0
        self.shows_updated = 0
        self.errors = 0

        shows = PodcastShow.objects.all()

        for show in shows:
            updated = self.__update_show(show)
            self.shows_processed += 1

            if updated:
                self.shows_updated += 1

        self.__show_stats()


    def __show_stats(self):
        output_message = f"""
Shows Processed : {self.shows_processed}
Shows Updated   : {self.shows_updated}

Errors          : {self.errors}
        """

        self.stdout.write(
            self.style.SUCCESS(output_message)
        )

    def __update_show(self, show: PodcastShow) -> bool:
        show_data = None
        updated = False

        try:
            show_data = feedparser.parse(show.feed_url)
            if show_data['status'] >= 400:
                self.errors += 1
                return
        except Exception as e:
            self.errors += 1
            self.stdout.write(
                self.style.ERROR(f"There was an error retrieving {show.feed_url}: {e}")
            )
            return

        if show_data['feed']['title'] != show.title:
            show.title = show_data['feed']['title']
            show.save()
            updated = True

        summary = show_data['feed']['summary'] \
            if 'summary' in show_data['feed'].keys() \
            else show_data['feed']['description']

        if summary and summary != show.description:
            show.description = summary
            show.save()
            updated = True

        if show_data['feed']['author'] != show.owner:
            show.owner = show_data['feed']['author']
            show.save()
            updated = True

        image_url = self.__get_show_image_url(show_data)
        image = self.__get_show_image(image_url)

        if image:
            show.show_image.save(image[0], image[1])
            updated = True

        return updated


    def __get_show_image_url(self, show_data: feedparser.FeedParserDict) -> Optional[str]:
        """
        Attempts to get the show image URL from the
        feed data.
        """
        if 'image' in show_data['feed'] and 'href' in show_data['feed']['image']:
            url = show_data['feed']['image']['href']
            url = url.split('?')[0]
            return url

        return None

    def __get_show_image(self, show_image_url: str) -> Optional[Tuple[str,File]]:
        """
        Attempts to download the show image from the provided URL
        """
        if not show_image_url:
            return None

        response = requests.get(show_image_url, stream=True, headers=self.HEADERS)

        if not response.ok:
            return None

        file_name = show_image_url.split('/')[-1]
        if all(sub not in file_name for sub in ['.jpeg', '.jpg', '.png', '.avif', '.webp']):
            file_name += '.jpg'

        lf = tempfile.NamedTemporaryFile()

        for block in response.iter_content(1024 * 8):
            if not block:
                break

            lf.write(block)

        return (file_name, File(lf))
