# -*- coding: utf-8 -*-


from django.conf import settings

from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic import ListView, UpdateView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from programs.models import Program, ProgramDescription, ProgramImportRecord

from core.filters import ProgramListFilterSet
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry

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
        if queryset is None:
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
    title = 'Dashboard'
    heading = 'Communicator Dashboard'
    local = settings.LOCAL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        last_import = ProgramImportRecord.objects.order_by('-start_date_time').first()

        ctx['import'] = {
            'last_import_date': last_import.start_date_time,
            'programs_created': last_import.programs_created_count,
            'programs_processed': last_import.programs_processed,
        }

        program_content_type = ContentType.objects.get_for_model(Program)
        program_description_content_type = ContentType.objects.get_for_model(ProgramDescription)

        user_events = LogEntry.objects.filter(
            Q(content_type=program_content_type)|Q(content_type=program_description_content_type),
            actor=user,
        )[:5]

        global_events = LogEntry.objects.filter(
            Q(content_type=program_content_type)|Q(content_type=program_description_content_type)
        ).exclude(
            actor=user
        )[:5]

        ctx['meta'] = {
            'program_count': user.meta.editable_programs.count(),
            'missing_desc_count': user.meta.programs_missing_descriptions_count,
            'missing_custom_desc_count': user.meta.programs_missing_custom_descriptions_count,
            'missing_career_paths': user.meta.programs_missing_career_paths_count
        }
        ctx['user_events'] = user_events
        ctx['global_events'] = global_events
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
