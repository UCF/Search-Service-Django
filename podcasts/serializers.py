from rest_framework import serializers

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

class PodcastShowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastShow

class PodcastEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastEpisode
