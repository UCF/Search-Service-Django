from django.conf.urls import url

from locations.views import LocationListView, LocationDetailView

urlpatterns = [
    url(r'^$', LocationListView.as_view(), name='api.locations.list'),
    url(r'^(?P<pk>\d+)/$', LocationDetailView.as_view(), name='api.locations.detail'),
]
