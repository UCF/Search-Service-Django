from django.conf.urls import url

from podcasts.views import (
    PodcastShowListView,
    PodcastShowDetailView,
    PodcastEpisodeListView,
    PodcastEpisodeSummaryView,
    PodcastShowEpisodeListView
)

urlpatterns = [
    url(r'^$',
        PodcastShowListView.as_view(),
        name='api.podcasts.list'
    ),
    url(r'^episodes/$',
        PodcastEpisodeListView.as_view(),
        name='api.podcasts.episodelist'
    ),
    url(r'^episodes/(?P<id>\d+)/$',
        PodcastEpisodeSummaryView.as_view(),
        name='api.podcasts.episode.summary'
    ),
    url(r'^(?P<id>\d+)/$',
        PodcastShowDetailView.as_view(),
        name='api.podcasts.detail'
    ),
    url(r'(?P<id>\d+)/episodes/$',
        PodcastShowEpisodeListView.as_view(),
        name='api.podcasts.details.episodelist'
    )
]
