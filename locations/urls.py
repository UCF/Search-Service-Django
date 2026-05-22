from django.conf.urls import url

from locations.views import LocationListView, LocationDetailView, LegacyLocationsView

urlpatterns = [
    url(r'^$', LocationListView.as_view(), name='api.locations.list'),
    url(r'^(?P<pk>\d+)/$', LocationDetailView.as_view(), name='api.locations.detail'),
    url(r'^legacy/$', LegacyLocationsView.as_view(), name='api.locations.legacy'),
]
