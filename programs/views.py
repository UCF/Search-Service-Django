# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
# from django_filters.rest_framework.filters import SearchFilter

from programs.models import *
from programs.serializers import *
from programs.filters import *


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
