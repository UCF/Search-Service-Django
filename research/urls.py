from django.conf.urls import url

from research.views import *

urlpatterns = [
    url(f'^researchers/',
        ResearcherListView.as_view(),
        name='api.researchers.list'
    )
]
