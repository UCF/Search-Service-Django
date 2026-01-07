from rest_framework import serializers
from django.urls import reverse

from taggit.serializers import (
    TaggitSerializer,
    TagListSerializerField
)

from podcasts.models import (
    PodcastShow,
    PodcastCategory,
    PodcastEpisodeHighlight,
    PodcastEpisode
)

class PodcastCategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastCategory

class PodcastShowSerializer(serializers.ModelSerializer):
    show_image = serializers.SerializerMethodField()
    episodes = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'title',
            'description',
            'show_image',
            'episodes'
        )
        model = PodcastShow

    def get_show_image(self, obj):
        return {
            'full': obj.show_image.url if obj.show_image else None,
            'medium': obj.show_image_medium.url if obj.show_image_medium else None,
            'thumbnail': obj.show_image_thumbnail.url if obj.show_image_thumbnail else None
        }

    def get_episodes(self, obj):
        return reverse(
            'api.podcasts.details.episodelist',
            args=[obj.id]
        )

class PodcastEpisodeHighlightSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PodcastEpisodeHighlight

class PodcastEpisodeSimpleSerializer(serializers.ModelSerializer):
    tags = TagListSerializerField(read_only=True)

    class Meta:
        fields = (
            'id',
            'title',
            'description',
            'tags',
            'category'
        )
        model = PodcastEpisode

class PodcastEpisodeIdSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
        )
        model = PodcastEpisode


class PodcastEpisodeSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(read_only=True)
    category = PodcastCategorySerializer(read_only=True, many=False)

    highlights = PodcastEpisodeHighlightSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = PodcastEpisode
