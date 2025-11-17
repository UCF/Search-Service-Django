from django.db import models
import feedparser

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
    show_image = models.ImageField()
    category = models.ForeignKey(PodcastCategory, related_name='podcasts', default=1, on_delete=models.CASCADE)
    objects = PodcastShowManager()

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
    transcript = models.TextField(null=True, blank=True)

    # Foreign Keys
    show = models.ForeignKey(PodcastShow, related_name='episodes', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

