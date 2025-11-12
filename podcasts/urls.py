from django.conf.urls import url

from podcasts.views import (
    PodcastShowListView,
    PodcastShowDetailView
)

urlpatterns = [
    url(r'^$',
        PodcastShowListView.as_view(),
        name='api.podcasts.list'
        ),
    url(r'^(?P<id>\d+)/$',
        PodcastShowDetailView.as_view(),
        name='api.podcasts.detail'
    ),
]
