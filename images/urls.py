from django.conf.urls import url, include

from images.views import *

urlpatterns = [
    url(r'^$',
        ImageListView.as_view(),
        name='api.images.list'
        ),
    url(r'^(?P<id>\d+)/$',
        ImageDetailView.as_view(),
        name='api.images.detail'
        ),
    url(r'^search/$',
        ImageSearchView.as_view(),
        name='api.images.search'
        )
]
