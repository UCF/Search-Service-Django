from django.conf.urls import url, include

from teledata.views import *

urlpatterns = [
    url(r'^buildings/$',
        BuildingListView.as_view(),
        name='api.buildings.list'
        ),
]