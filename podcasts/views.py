from rest_framework import generics
from django.http import Http404
from django.shortcuts import get_object_or_404

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

from podcasts.serializers import (
    PodcastShowSerializer,
    PodcastEpisodeSerializer
)

from podcasts.filters import (
    PodcastShowListFilter,
    PodcastEpisodeListFilter
    )

# Create your views here.
class PodcastShowListView(generics.ListAPIView):
    queryset = PodcastShow.objects.all()
    serializer_class = PodcastShowSerializer
    filter_class = PodcastShowListFilter


class PodcastShowDetailView(generics.RetrieveAPIView):
    queryset = PodcastShow.objects.all()
    lookup_field = 'id'
    serializer_class = PodcastShowSerializer

class PodcastEpisodeListView(generics.ListAPIView):
    queryset = PodcastEpisode.objects.all()
    lookup_field = 'id'
    serializer_class = PodcastEpisodeSerializer
    filter_class = PodcastEpisodeListFilter

class PodcastShowEpisodeListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = PodcastEpisodeSerializer
    filter_class = PodcastEpisodeListFilter

    def get_queryset(self):
        show_id = self.kwargs.get('id', None)
        if not show_id:
            return Http404

        show = get_object_or_404(PodcastShow, pk=show_id)
        return PodcastEpisode.objects.filter(show=show)
