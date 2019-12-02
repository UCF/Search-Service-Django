# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import resolve

from django.views.generic.base import TemplateView
from core.views import TitleContextMixin

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

# Documentation Views
class TeledataMenuMixin(object):
    pages = [
        ('docs.teledata.search', 'Teledata Search'),
        ('docs.teledata.staff.list', 'Staff List'),
        ('docs.teledata.organizations.list', 'Organization List'),
        ('docs.teledata.departments.list', 'Department List'),
        ('docs.teledata.buildings.list', 'Building List')
    ]

    def get_context_data(self, **kwargs):
        context = super(TeledataMenuMixin, self).get_context_data(**kwargs)
        page_list = []

        for page in self.pages:
            active = False
            url = reverse(page[0])

            if url == self.request.path:
                active = True

            page_list.append({
                'url': url,
                'text': page[1],
                'active': active
            })

        context['menu'] = page_list

        return context

class TeledataSearchDocView(TitleContextMixin, TeledataMenuMixin, TemplateView):
    template_name = 'teledata/docs/teledata-search.html'
    title = 'Teledata Documentation'
    heading = 'Teledata Search'

class TeledataStaffDocView(TitleContextMixin, TeledataMenuMixin, TemplateView):
    template_name = 'teledata/docs/teledata-staff-list.html'
    title = 'Staff List Documentation'
    heading = 'Staff List'

class TeledataOrganizationDocView(TitleContextMixin, TeledataMenuMixin, TemplateView):
    template_name = 'teledata/docs/teledata-org-list.html'
    title = 'Organizations Documentation'
    heading = 'Organization List'

class TeledataDepartmentDocView(TitleContextMixin, TeledataMenuMixin, TemplateView):
    template_name = 'teledata/docs/teledata-dept-list.html'
    title = 'Departments Documentation'
    heading = 'Department List'

class TeledataBuildingDocView(TitleContextMixin, TeledataMenuMixin, TemplateView):
    template_name = 'teledata/docs/teledata-bldg-list.html'
    title = 'Buildings List'
    heading = 'Building List'
