from django.db import models
from django.core.files import File
from taggit.managers import TaggableManager

from typing import Optional, Tuple

from core.storage_backends import PodcastImageStorage

import feedparser
import requests

from io import BytesIO
from PIL import Image as PILImage
from pathlib import Path

# Create your models here.
class PodcastShowManager(models.Manager):
    def add_show_from_rss(self, rss_feed_url: str):
        """
        Attempts to add a show from a provided RSS feed URL
        """
        try:
            feed = feedparser.parse(rss_feed_url)
            if feed['status'] >= 400:
                return None

            show = self.create(
                title=feed['feed']['title'],
                feed_url=rss_feed_url,
                description=feed['feed']['summary']
                    if 'summary' in feed['feed'].keys()
                    else feed['feed']['description'],
                owner=feed['feed']['author'],
            )

            return show
        except Exception as e:
            raise e

class PodcastCategory(models.Model):
    title = models.CharField(max_length=100, null=False, blank=False, db_index=True, unique=True)
    description = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.title


class PodcastShow(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False, db_index=True)
    feed_url = models.CharField(max_length=400, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    owner = models.CharField(max_length=255, null=False, blank=False)

    show_image = models.ImageField(
        storage=PodcastImageStorage,
        null=True,
        blank=True
    )

    show_image_thumbnail = models.ImageField(
        storage=PodcastImageStorage,
        null=True,
        blank=True,
        editable=False
    )

    show_image_medium = models.ImageField(
        storage=PodcastImageStorage,
        null=True,
        blank=True,
        editable=False
    )

    category = models.ForeignKey(PodcastCategory, related_name='podcasts', default=1, on_delete=models.CASCADE)
    tags = TaggableManager()
    objects = PodcastShowManager()

    def __make_thumbnail(self, width, height, name='') -> Optional[Tuple[bytearray, str]]:
        """
        Attempts to make a thumbnail of width and height
        from the primary show image.
        """
        img = None

        # See if we're using S3 for storage
        if 's3' in self.show_image.url:
            url = self.show_image.url

            # Read the file into an Image object
            response = requests.get(url)
            image_data = BytesIO(response.content)
            img = PILImage.open(image_data)
        else:
            img = self.show_image.file.copy()

        img_thumbnail = img.copy()

        path = Path(self.show_image.url)
        ext = path.suffix if path.suffix else '.jpg'
        format = img.format
        if ext in path.name:
            filename = path.name.replace(ext, f"{name}{ext}")
        else:
            filename = f"{path.name}{name}{ext}"

        if width and height:
            img_thumbnail.thumbnail((width, height))
            img_thumbnail.save(image_data, format=format)
        elif width and not height:
            original_width, original_height = img.size
            height = int(original_height * (width / original_width))
            img_thumbnail.thumbnail((width, height))
            img_thumbnail.save(image_data, format=format)

        image_data.seek(0)

        return (filename, image_data)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        update_fields = []

        if self.show_image and not (self.show_image_medium or self.show_image_thumbnail):
            thumbnail = self.__make_thumbnail(150, 150, '_thumbnail')
            if thumbnail:
                self.show_image_thumbnail.save(thumbnail[0], thumbnail[1], False)
                update_fields.append('show_image_thumbnail')

            medium = self.__make_thumbnail(300, None, '_medium')
            if medium:
                self.show_image_medium.save(medium[0], medium[1], False)
                update_fields.append('show_image_medium')

        if len(update_fields) > 0:
            super().save(update_fields=update_fields)

    def __str__(self):
        return self.title

class PodcastEpisode(models.Model):
    guid = models.CharField(max_length=255, null=False, blank=False, editable=False, db_index=True)
    title = models.CharField(max_length=255, null=False, blank=False, db_index=True)
    description = models.TextField(null=False, blank=False)
    published_date = models.DateField(null=False, blank=False)
    duration = models.DurationField(null=False, blank=False)
    link = models.URLField(null=True, blank=True)
    audio_file = models.URLField(null=False, blank=False)
    episode_type = models.CharField(max_length=10, null=False, blank=False)
    season_number = models.IntegerField(null=True, blank=True)
    episode_number = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)
    category = models.ForeignKey(PodcastCategory, related_name='episodes', default=1, on_delete=models.SET_DEFAULT)
    tags = TaggableManager()
    transcript = models.TextField(null=True, blank=True)

    # Foreign Keys
    show = models.ForeignKey(PodcastShow, related_name='episodes', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class PodcastEpisodeHighlight(models.Model):
    time_text = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    summary = models.TextField(blank=False, null=False)
    episode = models.ForeignKey(PodcastEpisode, related_name='highlights', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.episode.title}: Highlight {self.order}"
