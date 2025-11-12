from rest_framework import generics

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

from podcasts.serializers import (
    PodcastShowSerializer,
    PodcastEpisodeSerializer
)

# Create your views here.
class PodcastShowListView(generics.ListAPIView):
    queryset = PodcastShow.objects.all()
    serializer_class = PodcastShowSerializer


class PodcastShowDetailView(generics.RetrieveAPIView):
    queryset = PodcastShow.objects.all()
    lookup_field = 'id'
    serializer_class = PodcastShowSerializer
