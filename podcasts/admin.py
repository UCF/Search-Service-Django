from django.contrib import admin

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

# Register your models here.
@admin.register(PodcastShow)
class PodcastShowAdmin(admin.ModelAdmin):
    pass

@admin.register(PodcastEpisode)
class PodcastEpisodeAdmin(admin.ModelAdmin):
    pass
