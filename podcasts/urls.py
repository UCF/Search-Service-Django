from django.conf.urls import url

from podcasts.views import (
    PodcastShowListView,
    PodcastShowDetailView,
    PodcastEpisodeListView,
    PodcastEpisodeSummaryView,
    PodcastShowEpisodeListView,
    PodcastCategoryListView,
    PodcastCategoryDetailView
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
    url(r'^categories/$',
        PodcastCategoryListView.as_view(),
        name='api.podcasts.categories.list'
    ),
    url(r'^categories/(?P<slug>[a-zA-Z\-]+)/$',
        PodcastCategoryDetailView.as_view(),
        name='api.podcasts.categories.detail'
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
