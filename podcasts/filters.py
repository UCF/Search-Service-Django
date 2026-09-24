from django_filters import rest_framework as filters
from django.db.models import Q

from core.utils.filter_utils import any_iexact, split_list_param
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
            any_iexact('tags__name', split_list_param(value))
        ).distinct()

class PodcastEpisodeListFilter(filters.FilterSet):
    search = filters.CharFilter(method='custom_episode_search', label='Search')
    tags = filters.CharFilter(method='custom_tag_search', label='Tags')
    category = filters.CharFilter(method='custom_category_search', label='Category')
    show = filters.NumberFilter(method='custom_show_search', label='Show ID')
    format = filters.CharFilter(method='custom_format', label='Format')

    class Meta:
        model = PodcastEpisode
        fields = (
            'search',
            'show',
            'category',
            'tags'
        )

    def custom_episode_search(self, queryset, name, value):
        """
        Very broad search using all available search vectors
        on episodes.
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(category__title__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()

    def custom_category_search(self, queryset, name, value):
        return queryset.filter(
            category__title__iexact=value
        )

    def custom_show_search(self, queryset, name, value):
        return queryset.filter(
            show__id=value
        )


    def custom_tag_search(self, queryset, name, value):
        return queryset.filter(
            any_iexact('tags__name', split_list_param(value))
        ).distinct()

