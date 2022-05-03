# -*- coding: utf-8 -*-


from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from locations.models import *
from locations.serializers import *
# from locations.filters import *

from rest_framework.filters import OrderingFilter


# Create your views here.

class CampusTypeListView(generics.ListAPIView):
    queryset = CampusType.objects.all()
    serializer_class = CampusTypeSerializer


class CampusListView(generics.ListAPIView):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer


class FacilityListView(generics.ListAPIView):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer


class ParkingLotListView(generics.ListAPIView):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer


class ParkingPermitTypeListView(generics.ListAPIView):
    queryset = ParkingPermitType.objects.all()
    serializer_class = ParkingPermitTypeSerializer


class ParkingZoneListView(generics.ListAPIView):
    queryset = ParkingZone.objects.all()
    serializer_class = ParkingZoneSerializer


class LocationTypeListView(generics.ListAPIView):
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer


class LocationListView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class PointTypeListView(generics.ListAPIView):
    queryset = PointType.objects.all()
    serializer_class = PointTypeSerializer


class PointOfInterestListView(generics.ListAPIView):
    queryset = PointOfInterest.objects.all()
    serializer_class = PointOfInterestSerializer


class GroupTypeListView(generics.ListAPIView):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
