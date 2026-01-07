from rest_framework import generics
from django.http import Http404
from django.shortcuts import get_object_or_404

from podcasts.models import (
    PodcastShow,
    PodcastEpisode,
    PodcastCategory
)

from podcasts.serializers import (
    PodcastShowSerializer,
    PodcastEpisodeSerializer,
    PodcastEpisodeSimpleSerializer,
    PodcastEpisodeIdSerializer,
    PodcastCategorySerializer
)

from podcasts.filters import (
    PodcastShowListFilter,
    PodcastEpisodeListFilter
)

# Create your views here.
class PodcastShowListView(generics.ListAPIView):
    """
    The generic list view for all podcast shows.
    """
    queryset = PodcastShow.objects.all()
    serializer_class = PodcastShowSerializer
    filter_class = PodcastShowListFilter


class PodcastShowDetailView(generics.RetrieveAPIView):
    """
    The per show detail view
    """
    queryset = PodcastShow.objects.all()
    lookup_field = 'id'
    serializer_class = PodcastShowSerializer


class PodcastEpisodeListView(generics.ListAPIView):
    """
    A general, searchable episode list view for podcast
    episodes.
    """
    queryset = PodcastEpisode.objects.all()
    lookup_field = 'id'
    filter_class = PodcastEpisodeListFilter

    def get_serializer_class(self):
        if self.request.query_params.get('fields', None) == 'id':
            return PodcastEpisodeIdSerializer

        return PodcastEpisodeSerializer

class PodcastEpisodeSummaryView(generics.RetrieveAPIView):
    """
    A detail view for podcast episodes
    """
    queryset = PodcastEpisode.objects.all()
    lookup_field = 'id'
    serializer_class = PodcastEpisodeSerializer


class PodcastShowEpisodeListView(generics.ListAPIView):
    """
    A list view for podcasts filtered by the show id provided
    in the API url path
    """
    lookup_field = 'id'
    filter_class = PodcastEpisodeListFilter

    def get_queryset(self):
        show_id = self.kwargs.get('id', None)
        if not show_id:
            return Http404

        show = get_object_or_404(PodcastShow, pk=show_id)
        return PodcastEpisode.objects.filter(show=show)

    def get_serializer_class(self):
        if self.request.query_params.get('fields', None) == 'id':
            return PodcastEpisodeIdSerializer

        return PodcastEpisodeSerializer

class PodcastCategoryListView(generics.ListAPIView):
    """
    A list view for all podcast categories
    """
    queryset = PodcastCategory.objects.all()
    serializer_class = PodcastCategorySerializer


class PodcastCategoryDetailView(generics.RetrieveAPIView):
    """
    A detail view for podcast categories
    """
    queryset = PodcastCategory.objects.all()
    lookup_field = 'slug'
    serializer_class = PodcastCategorySerializer
