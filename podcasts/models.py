from django.db import models

# Create your models here.
class PodcastShow(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    feed_url = models.CharField(max_length=400, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    owner = models.CharField(max_length=255, null=False, blank=False)
    show_image = models.ImageField()

    def __str__(self):
        return self.title

class PodcastEpisode(models.Model):
    guid = models.UUIDField(null=False, blank=False, editable=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    published_date = models.DateField(null=False, blank=False)
    duration = models.DurationField(null=False, blank=False)
    link = models.URLField(null=False, blank=False)
    audio_file = models.URLField(null=False, blank=False)
    episode_type = models.CharField(max_length=10, null=False, blank=False)
    season_number = models.IntegerField(null=True, blank=True)
    episode_number = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)

    # Foreign Keys
    show = models.ForeignKey(PodcastShow, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

