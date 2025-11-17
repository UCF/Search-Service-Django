from django_filters import rest_framework as filters
from django.db.models import Q

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

class PodcastShowListFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='title', lookup_expr='icontains')
    tags = filters.CharFilter(method='custom_tag_search', label='Tags')

    class Meta:
        model = PodcastShow
        fields = (
            'search',
            'category',
            'tags',
        )

    def custom_tag_search(self, queryset, name, value):
        return queryset.filter(
            tags__name__in=value
        )

class PodcastEpisodeListFilter(filters.FilterSet):
    search = filters.CharFilter(method='custom_episode_search', label='Search')
    tags = filters.CharFilter(method='custom_tag_search', label='Tags')

    class Meta:
        model = PodcastEpisode
        fields = (
            'search',
            'category',
            'tags',
        )

    def custom_episode_search(self, queryset, name, value):
        """
        Very broad search using all available search vectors
        on episodes.
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(category__name__icontains=value) |
            Q(tags__name__icontains=value)
        )

    def custom_tag_search(self, queryset, name, value):
        return queryset.filter(
            tags__name__in=value
        )

