from rest_framework import serializers

from podcasts.models import (
    PodcastShow,
    PodcastEpisodeHighlight,
    PodcastEpisode
)

class PodcastShowSerializer(serializers.ModelSerializer):
    show_image = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = PodcastShow

    def get_show_image(self, obj):
        return {
            'full': obj.show_image.url if obj.show_image else None,
            'medium': obj.show_image_medium.url if obj.show_image_medium else None,
            'thumbnail': obj.show_image_thumbnail.url if obj.show_image_thumbnail else None
        }

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
