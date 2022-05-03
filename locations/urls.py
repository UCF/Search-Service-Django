from django.conf.urls import url, include

from locations.views import *

urlpatterns = [
    url(r'^campuses/$',
        CampusListView.as_view(),
        name='api.campuses.list'
        ),
    url(
        r'^campuses/types/$',
        CampusTypeListView.as_view(),
        name='api.campuses.types.list'
        ),
    url(r'^facilities/$',
        FacilityListView.as_view(),
        name='api.facilities.list'
        ),
    url(r'^parking/$',
        ParkingLotListView.as_view(),
        name='api.parking.list'
        ),
    url(r'^parking/permit-types/$',
        ParkingPermitTypeListView.as_view(),
        name='api.parking.permittypes.list'
        ),
    url(r'^parking/zones/$',
        ParkingZoneListView.as_view(),
        name='api.parking.zones.list'
        ),
    url(r'^locations/$',
        LocationListView.as_view(),
        name='api.locations.list'
        ),
    url(r'^locations/types/$',
        LocationTypeListView.as_view(),
        name='api.locations.types.list'
        ),
    url(r'^points-of-interest/$',
        PointOfInterestListView.as_view(),
        name='api.pointsofinterest.list'
        ),
    url(r'^points-of-interest/types/$',
        PointTypeListView.as_view(),
        name='api.pointsofinterest.types.list'
        ),
    url(r'^groups/$',
        GroupListView.as_view(),
        name='api.groups.list'
        ),
    url(r'^groups/types/$',
        GroupTypeListView.as_view(),
        name='api.groups.types.list'
        ),
]
