from django.conf.urls import url

from research.views import *

urlpatterns = [
    url(r'^researchers/$',
        ResearcherListView.as_view(),
        name='api.researchers.list'
    ),
    url(r'^researchers/(?P<id>\d+)/works/$',
        ResearchWorkListView.as_view(),
        name='api.researcher.works.list'
    )
]
