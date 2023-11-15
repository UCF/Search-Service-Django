# -*- coding: utf-8 -*-


from django.conf import settings

from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from programs.models import Program

from core.filters import ProgramListFilterSet

import settings

class TitleContextMixin(object):
    """
    Mixin for setting title and heading
    """
    def get_context_data(self, **kwargs):
        context = super(TitleContextMixin, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['heading'] = self.heading
        context['local'] = self.local

        return context

class FilteredListView(ListView):
    filterset = None

    def get_queryset(self, queryset=None):
        if not queryset:
            queryset = super().get_queryset()
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context

# Create your views here.
class HomeView(TitleContextMixin, TemplateView):
    template_name = 'home.html'
    title = ''
    heading = 'UCF Search Service'
    local = settings.LOCAL


class SearchView(LoginRequiredMixin, TitleContextMixin, TemplateView):
    template_name = 'search.html'
    title = ''
    heading = 'UCF Search Service'
    local = settings.LOCAL

class SettingsAPIView(APIView):
    def get(request, format=None, **kwargs):
        return Response({
            'ucf_news_api': settings.UCF_NEWS_API,
            'ucf_events_api': settings.UCF_EVENTS_API,
            'ucf_search_service_api': settings.UCF_SEARCH_SERVICE_API
        })

# Communicator Dashboard Views
class CommunicatorDashboard(LoginRequiredMixin, TitleContextMixin, TemplateView):
    template_name = 'dashboard/home.html'
    title = ''
    heading = 'Communicator Dashboard'
    local = settings.LOCAL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['most_recent_import'] = user.meta.editable_programs.latest('modified').modified
        ctx['recently_added'] = user.meta.editable_programs.order_by('-created')[:10]
        ctx['meta'] = {
            'program_count': user.meta.editable_programs.count(),
            'missing_desc_count': user.meta.programs_missing_descriptions_count
        }
        return ctx


class ProgramListing(LoginRequiredMixin, TitleContextMixin, FilteredListView):
    template_name = 'dashboard/program-list.html'
    title = 'Programs'
    heading = 'Programs'
    local = settings.LOCAL
    filterset_class = ProgramListFilterSet
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset(self.request.user.meta.editable_programs)

class ProgramEditView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    template_name = 'dashboard/program-edit.html'
    title = 'Edit Program'
    heading = 'Edit Program'
    local = settings.LOCAL
    fields = ('name',)

    def get_queryset(self):
        return self.request.user.meta.editable_programs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj: Program = ctx['object']
        ctx['read_only_fields'] = {
            'Name': obj.name,
            'Credit Hours': obj.credit_hours,
            'Plan Code': obj.plan_code,
            'Subplan Code': obj.subplan_code,
            'CIP': obj.current_cip,
            'Catalog URL': obj.catalog_url,
            'Colleges': obj.colleges,
            'Departments': obj.departments,
            'Level': obj.level,
            'Career': obj.career,
            'Degree': obj.degree,
            'Online': obj.online,
            'Created': obj.created,
            'Last Modified': obj.modified,
            'Resident Tuition': obj.resident_tuition,
            'Non-Resident Tuition': obj.nonresident_tuition,
            'Active': obj.active,
            'Graduate Slate ID': obj.graduate_slate_id,
            'Valid': obj.valid
        }
        return ctx
