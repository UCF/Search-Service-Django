# -*- coding: utf-8 -*-
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from locations.models import Location
from locations.serializers import LocationSerializer, LegacyLocationSerializer


class LocationListView(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['object_type', 'visible', 'private', 'is_verified']


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class LegacyLocationsView(APIView):
    """
    Reproduces the map.ucf.edu/locations.json feed format.
    Returns all visible locations serialized in the legacy structure
    expected by the UCF Location CPT Plugin importer.
    """
    renderer_classes = [JSONRenderer]

    def get(self, request, format=None):
        locations = Location.objects.filter(visible=True)
        serializer = LegacyLocationSerializer(
            locations,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
