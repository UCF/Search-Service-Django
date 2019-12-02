# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from teledata.models import *
from teledata.serializers import *
from teledata.filters import *
from teledata.pagination import BackwardsCompatiblePagination

from rest_framework.filters import OrderingFilter

# Create your views here.
class BuildingListView(generics.ListAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailView(generics.RetrieveAPIView):
    queryset = Department.objects.all()
    lookup_field = 'id'
    serializer_class = DepartmentSerializer


class OrganizationListView(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class StaffListView(generics.ListAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class CombinedTeledataListView(generics.ListAPIView):
    queryset = CombinedTeledata.objects.all()
    serializer_class = CombinedTeledataSerializer

class CombinedTeledataSearchView(CombinedTeledataListView):
    filter_class = CombinedTeledataFilter
    filter_backends = [DjangoFilterBackend,OrderingFilter]
    pagination_class = BackwardsCompatiblePagination
    ordering_fields = ['id', 'score']
    ordering = ['-score']

    def get_queryset(self):
        if self.request.GET.get('search') is not None:
            return CombinedTeledata.objects.search(self.request.GET.get('search'))
        else:
            return CombinedTeledata.objects.none()
