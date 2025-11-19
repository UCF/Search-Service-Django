from django.contrib import admin

from podcasts.models import (
    PodcastShow,
    PodcastEpisode,
    PodcastEpisodeHighlight
)

# Register your models here.
class PodcastEpisodeHighlightInline(admin.TabularInline):
    model = PodcastEpisodeHighlight
    extra = 1

@admin.register(PodcastShow)
class PodcastShowAdmin(admin.ModelAdmin):
    pass

@admin.register(PodcastEpisode)
class PodcastEpisodeAdmin(admin.ModelAdmin):
    inlines = [PodcastEpisodeHighlightInline]
