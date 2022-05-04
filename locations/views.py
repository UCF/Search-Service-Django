# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from locations.models import *
from locations.serializers import *
# from locations.renderers import *


# Create your views here.

class KMLViewMixin(object):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = ''
    kml_filename = ''

    def get(self, request, *args, **kwargs):
        resp = Response(
            {'data': self.queryset.all()},
            template_name=self.template_name,
            content_type='application/vnd.google-earth.kml+xml',
            headers={
                'Content-Type': 'application/vnd.google-earth.kml+xml',
                'Content-Disposition': 'attachment; filename="{0}"'.format(self.kml_filename)
            }
        )
        return resp


class CampusTypeListView(generics.ListAPIView):
    queryset = CampusType.objects.all()
    serializer_class = CampusTypeSerializer


class CampusListView(generics.ListAPIView):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer


class CampusListKMLView(KMLViewMixin, CampusListView):
    template_name = 'locations/campuses.kml'
    kml_filename = 'campuses.kml'


class FacilityListView(generics.ListAPIView):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer


class FacilityListKMLView(KMLViewMixin, FacilityListView):
    template_name = 'locations/facilities.kml'
    kml_filename = 'facilities.kml'


class ParkingLotListView(generics.ListAPIView):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer


class ParkingLotListKMLView(KMLViewMixin, ParkingLotListView):
    template_name = 'locations/parkinglots.kml'
    kml_filename = 'parking.kml'


class ParkingPermitTypeListView(generics.ListAPIView):
    queryset = ParkingPermitType.objects.all()
    serializer_class = ParkingPermitTypeSerializer


class ParkingZoneListView(generics.ListAPIView):
    queryset = ParkingZone.objects.all()
    serializer_class = ParkingZoneSerializer


class ParkingZoneListKMLView(KMLViewMixin, ParkingZoneListView):
    template_name = 'locations/parkingzones.kml'
    kml_filename = 'parkingzones.kml'


class LocationTypeListView(generics.ListAPIView):
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer


class LocationListView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class LocationListKMLView(KMLViewMixin, LocationListView):
    template_name = 'locations/locations.kml'
    kml_filename = 'locations.kml'


class PointTypeListView(generics.ListAPIView):
    queryset = PointType.objects.all()
    serializer_class = PointTypeSerializer


class PointOfInterestListView(generics.ListAPIView):
    queryset = PointOfInterest.objects.all()
    serializer_class = PointOfInterestSerializer


class PointOfInterestListKMLView(KMLViewMixin, PointOfInterestListView):
    template_name = 'locations/pointsofinterest.kml'
    kml_filename = 'pointsofinterest.kml'


class GroupTypeListView(generics.ListAPIView):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupListKMLView(KMLViewMixin, GroupListView):
    template_name = 'locations/groups.kml'
    kml_filename = 'groups.kml'
