# -*- coding: utf-8 -*-


from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
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

class CoreAPI(APIView):

    def get(self, request, format=None):
        return Response({
            'programs': reverse('api.programs.list', request=request),
            'programs-search': reverse('api.programs.search', request=request),
            'colleges': reverse('api.colleges.list', request=request),
            'colleges-search': reverse('api.colleges.search', request=request),
            'departments': reverse('api.departments.list', request=request),
            'departments-search': reverse('api.departments.search', request=request),
            'descriptions-create': reverse('api.descriptions.create', request=request),
            'descriptionTypes': reverse('api.descriptions.types.list', request=request),
            'profiles-create': reverse('api.profiles.create', request=request),
            'profileTypes': reverse('api.profiles.types.list', request=request),
            'college-mappings': reverse('api.collegeoverride.list', request=request),
            'tuition-mappings': reverse('api.tuitionoverride.list', request=request)
        })

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


class ProgramProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = ProgramProfile.objects.all()
    lookup_field = 'id'
    serializer_class = ProgramProfileSerializer


class ProgramProfileCreateView(generics.CreateAPIView):
    serializer_class = ProgramProfileWriteSerializer


class ProgramProfileTypeListView(generics.ListAPIView):
    queryset = ProgramProfileType.objects.all()
    serializer_class = ProgramProfileTypeSerializer


class ProgramDescriptionDetailView(generics.RetrieveUpdateAPIView):
    queryset = ProgramDescription.objects.all()
    lookup_field = 'id'
    serializer_class = ProgramDescriptionSerializer


class ProgramDescriptionCreateView(generics.CreateAPIView):
    serializer_class = ProgramDescriptionWriteSerializer


class ProgramDescriptionTypeListView(generics.ListAPIView):
    queryset = ProgramDescriptionType.objects.all()
    serializer_class = ProgramDescriptionTypeSerializer

class CollegeOverrideListView(generics.ListAPIView):
    queryset = CollegeOverride.objects.all()
    serializer_class = CollegeOverrideSerializer

class TuitionOverrideListView(generics.ListAPIView):
    queryset = TuitionOverride.objects.all()
    serializer_class = TuitionOverrideSerializer
    filter_class = TuitionOverrideFilter

class TuitionOverrideCreateView(generics.CreateAPIView):
    serializer_class = TuitionOverrideSerializer

class TuitionOverrideDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TuitionOverride.objects.all()
    lookup_field = 'id'
    serializer_class = TuitionOverrideSerializer
