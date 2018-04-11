from django.conf.urls import url, include

from programs.views import *

urlpatterns = [
    url(r'^programs/$', ProgramListView.as_view(), name='programs.api.list'),
]
