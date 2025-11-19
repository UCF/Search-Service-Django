from rest_framework import serializers

from podcasts.models import (
    PodcastShow,
    PodcastEpisodeHighlight,
    PodcastEpisode
)

class PodcastShowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastShow

class PodcastEpisodeHighlightSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastEpisodeHighlight

class PodcastEpisodeSerializer(serializers.ModelSerializer):
    highlights = PodcastEpisodeHighlightSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = PodcastEpisode
