# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend

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

class LimitedPaginationMixin(LimitOffsetPagination):
    default_limit = 25
    max_limit = 50

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
            'tuition-mappings': reverse('api.tuitionoverride.list', request=request),
            'images': reverse('api.images.list', request=request),
            'images-search': reverse('api.images.search', request=request),
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
    pagination_class = LimitedPaginationMixin


class ProgramSearchView(ProgramListView):
    filter_class = ProgramFilter
    pagination_class = LimitedPaginationMixin


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

class CIPListView(generics.ListAPIView):
    queryset = CIP.objects.all()
    serializer_class = CIPSerializer
    pagination_class = LimitedPaginationMixin

class CIPDetailView(generics.RetrieveAPIView):
    queryset = CIP.objects.all()
    lookup_field = 'code'
    serializer_class = CIPSerializer

    def get_object(self):
        version = self.kwargs['version'] if 'version' in self.kwargs.keys() else settings.CIP_CURRENT_VERSION
        code = str(self.kwargs['code'])
        return CIP.objects.get(version=version, code=code)

class ProgramOutcomeView(APIView):
    def get(self, request, format=None, **kwargs):
        program = Program.objects.get(id=kwargs['id'])
        outcomes = program.outcomes.all()
        latest = program.outcomes.order_by('-academic_year__code').first()

        retval = {
            'by_year': ProgramOutcomeStatSerializer(instance=outcomes, many=True).data,
            'latest': ProgramOutcomeStatSerializer(instance=latest, many=False).data
        }

        return Response(retval)

class ProgramProjectionTotalsView(APIView):
    def get(request, format=None, **kwargs):
        program = Program.objects.get(id=kwargs['id'])

        obj = program.current_projections.aggregate(
            begin_employment=Sum('begin_employment'),
            end_employment=Sum('end_employment'),
            change=Sum('change'),
            change_percentage=Avg('change_percentage'),
            openings=Sum('openings')
        )

        first_projection = program.current_projections.first()

        obj['begin_year'] = first_projection.report_year_begin if first_projection is not None else None
        obj['end_year'] = first_projection.report_year_end if first_projection is not None else None

        serializer = EmploymentProjectionTotalsSerializer(obj, many=False)
        return Response(serializer.data)

class ProgramCareerView(APIView):
    def get(request, format=None, **kwargs):
        program = Program.objects.get(id=kwargs['id'])

        return Response(program.careers.all())
