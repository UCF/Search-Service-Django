# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
# from django_filters.rest_framework.filters import SearchFilter

from programs.models import *
from programs.serializers import *
from programs.filters import *


# Mixins
class MultipleFieldLookupMixin(object):
    """
    Multiple field lookups. Set multiple fields by providing `lookup_fields` tuple
    """
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:
                filter[field] = self.kwargs[field]

        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj


# Create your views here.
class CollegeListView(generics.ListAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer


class CollegeDetailView(generics.RetrieveAPIView):
    queryset = College.objects.all()
    lookup_field = 'id'
    serializer_class = CollegeSerializer


class CollegeSearchView(CollegeListView):
    filter_class = CollegeFilter


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailView(generics.RetrieveAPIView):
    queryset = Department.objects.all()
    lookup_field = 'id'
    serializer_class = DepartmentSerializer


class DepartmentSearchView(DepartmentListView):
    filter_class = DepartmentFilter


class ProgramListView(generics.ListAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer


class ProgramSearchView(ProgramListView):
    filter_class = ProgramFilter


class ProgramDetailView(generics.RetrieveAPIView):
    queryset = Program.objects.all()
    lookup_field = 'id'
    serializer_class = ProgramSerializer


class ProgramDescriptionListView(generics.ListCreateAPIView):
    queryset = ProgramDescription.objects.all()
    serializer_class = ProgramDescriptionSerializer

    def get_queryset(self):
        queryset = ProgramDescription.objects.all()

        if self.kwargs['program__id']:
            program_id = self.kwargs['program__id']
            queryset = queryset.filter(program__id=program_id)

        return queryset

class ProgramDescriptionDetailView(MultipleFieldLookupMixin, generics.RetrieveUpdateAPIView):
    queryset = ProgramDescription.objects.all()
    lookup_fields = ('program__id', 'description_type__id')
    serializer_class = ProgramDescriptionSerializer
