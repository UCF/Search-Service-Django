# -*- coding: utf-8 -*-


from typing import Any
from django.conf import settings
from django.contrib import messages
from django.utils import timezone

from django.shortcuts import render, resolve_url
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.views.generic.base import TemplateView
from django.views.generic import ListView, FormView
from django.db.models import Q, Count, Max
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from programs.models import (
    Program,
    ProgramDescription,
    ProgramDescriptionType,
    ProgramImportRecord,
    JobPosition
)
from programs.utilities.scheduling import get_next_date_from_cron
from core.forms import CommunicatorProgramForm

from core.filters import ProgramListFilterSet
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry

import settings
import json
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup

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
    title = 'Contributor Dashboard'
    heading = 'Contributor Dashboard'
    local = settings.LOCAL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        last_import = ProgramImportRecord.objects.order_by('-start_date_time').first()
        next_import = get_next_date_from_cron(settings.IMPORT_CRON)

        if last_import is not None:
            ctx['import'] = {
                'last_import_date': last_import.start_date_time,
                'programs_created': last_import.programs_created_count,
                'programs_processed': last_import.programs_processed,
            }
        else:
            ctx['import'] = {
                'last_import_date': None,
                'programs_created': None,
                'programs_processed': None,
            }

        if next_import:
            ctx['import']['next_import_date'] = next_import
        else:
            ctx['import']['next_import_date'] = None

        program_content_type = ContentType.objects.get_for_model(Program)
        program_description_content_type = ContentType.objects.get_for_model(ProgramDescription)

        user_events = LogEntry.objects.filter(
            Q(content_type=program_content_type)|Q(content_type=program_description_content_type),
            actor=user,
        ).values(
            'object_id',
            'actor__first_name',
            'actor__last_name'
        ).annotate(
            action_count=Count('object_id', distinct=True),
            newest_action=Max('timestamp'),
            max_id=Max('id')
        ).order_by(
            '-newest_action'
        )[:10]

        global_events = LogEntry.objects.filter(
            Q(content_type=program_content_type)|Q(content_type=program_description_content_type)
        ).exclude(
            actor=user
        ).values(
            'object_id',
            'actor__first_name',
            'actor__last_name'
        ).annotate(
            action_count=Count('object_id', distinct=True),
            newest_action=Max('timestamp'),
            max_id=Max('id')
        ).order_by(
            '-newest_action'
        )[:10]

        ctx['meta'] = {
            'program_count': user.meta.editable_programs.count(),
            'missing_desc_count': user.meta.programs_missing_descriptions_count,
            'missing_custom_desc_count': user.meta.programs_missing_custom_descriptions_count,
            'missing_jobs': user.meta.programs_missing_jobs_count
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

    def get_context_data(self, **kwargs):
        user = self.request.user

        ctx = super().get_context_data(**kwargs)
        ctx['meta'] = {
            'program_count': user.meta.editable_programs.count(),
            'missing_desc_count': user.meta.programs_missing_descriptions_count,
            'missing_custom_desc_count': user.meta.programs_missing_custom_descriptions_count,
            'missing_jobs': user.meta.programs_missing_jobs_count
        }

        return ctx

class ProgramEditView(LoginRequiredMixin, TitleContextMixin, FormView):
    template_name = 'dashboard/program-edit.html'
    title = 'Edit Program'
    heading = 'Edit Program'
    local = settings.LOCAL
    form_class = CommunicatorProgramForm

    def __get_program(self):
        """
        Gets the program from the pk passed in
        """
        retval = None
        program_pk = self.kwargs.get('pk', None)

        if program_pk is None:
            return retval

        try:
            retval = Program.objects.get(pk=program_pk)
        except Program.DoesNotExist:
            return retval

        return retval


    def __get_custom_description(self):
        """
        Gets the custom description of
        the program
        """
        program = self.__get_program()

        if not program or not program.has_custom_description:
            return None

        return ProgramDescription.objects.get(
            description_type=settings.CUSTOM_DESCRIPTION_TYPE_ID,
            program=program
        )

    def __get_description_by_name(self, program=None, description_type_name=None):
        """
        Gets the full description of
        the program
        """
        if not program or description_type_name is None:
            return None

        try:
            return ProgramDescription.objects.get(
                description_type__name=description_type_name,
                program=program
            )
        except ProgramDescription.DoesNotExist:
            return None

    def __get_jobs(self) -> str:
        """
        Returns a list of assigned jobs
        """
        program = self.__get_program()

        if not program:
            return ""

        return ",".join([x.name for x in program.jobs.all()])


    def __get_jobs_source(self) -> str:
        """
        Returns the jobs_source value
        """
        program = self.__get_program()

        if not program:
            return ""

        try:
            return program.audit_data.jobs_source
        except ObjectDoesNotExist:
            return ""

    def __get_highlights(self) -> str:
        """
        Returns the highlights json
        """
        program = self.__get_program()

        if not program:
            return ""
        try:
            return program.highlights
        except ObjectDoesNotExist:
            return ""

    def get_success_url(self) -> str:
        """
        Returns the success URL
        """
        program_pk = self.kwargs.get('pk', None)
        return resolve_url('dashboard.programs.edit', pk=program_pk)


    def get_initial(self):
        """
        Gets the initial values for the form
        """
        initial = super().get_initial()

        custom_description = self.__get_custom_description()
        jobs = self.__get_jobs()
        jobs_source = self.__get_jobs_source()
        highlights = self.__get_highlights()

        if custom_description:
            initial['custom_description'] = custom_description.description

        if jobs:
            initial['jobs'] = jobs

        if jobs_source:
            initial['jobs_source'] = jobs_source

        if highlights:
            initial['highlights'] = json.dumps(highlights)

        return initial

    def form_valid(self, form):
        """
        Runs whenever the form is submitted and
        all values provided pass validation.
        """
        program = self.__get_program()
        custom_description = self.__get_custom_description()

        if not custom_description:
            custom_description = ProgramDescription(
                description=form.cleaned_data['custom_description'],
                description_type=ProgramDescriptionType.objects.get(pk=settings.CUSTOM_DESCRIPTION_TYPE_ID),
                program=program
            )
        else:
            custom_description.description = form.cleaned_data['custom_description']

        custom_description.save()

        jobs_source = form.cleaned_data['jobs_source']
        audit_data = program.audit_data
        audit_data.jobs_source = jobs_source
        audit_data.save()

        current_jobs = self.__get_jobs().split(',')
        jobs = form.cleaned_data['jobs'].split(',')

        highlights = form.cleaned_data['highlights']
        highlights_list = json.loads(highlights)

        # Filter out entries with empty 'icon_class' or 'description'
        filtered_highlights = [entry for entry in highlights_list if entry['icon_class'] or entry['description']]
        if filtered_highlights:
            program.highlights = filtered_highlights
            program.save()
        if not filtered_highlights:
            program.highlights = []
            program.save()

        # Remove jobs that are no longer listed
        for job in current_jobs:
            if job not in jobs and job != '':
                job_position = JobPosition.objects.get(name=job.strip())
                program.jobs.remove(job_position)

        # Add new jobs
        for job in jobs:
            if job.strip() not in current_jobs:
                try:
                    job_position = JobPosition.objects.get(name=job.strip())
                except JobPosition.DoesNotExist:
                    job_position = JobPosition(name=job.strip())
                    job_position.save()

                program.jobs.add(job_position)

        # Final sanity check. If the description is empty,
        # delete the description because it might as well
        # not exist
        if custom_description.description == '':
            custom_description.delete()

        messages.success(self.request, self.__get_success_message(program))

        return super().form_valid(form)

    def __get_success_message(self, program):
        """
        Generates the success message
        """
        next_import_date = get_next_date_from_cron(settings.IMPORT_CRON)

        return f"You have successfully updated the {program.name} program. The changes will be available for the next degree import, which occurs on {next_import_date.strftime('%B %-d, %Y')}."


    def get_queryset(self):
        """
        Gets the initial queryset of the view
        """
        return self.request.user.meta.editable_programs

    def get_context_data(self, **kwargs):
        """
        Generates the context data of the view
        """
        ctx = super().get_context_data(**kwargs)

        program_pk = self.kwargs.get('pk', None)

        if program_pk is None:
            raise Http404

        try:
            object = Program.objects.get(pk=program_pk)
            self.object = object
            ctx['object'] = object
        except Program.DoesNotExist:
            raise Http404

        obj: Program = ctx['object']

        catalog_description = self.__get_description_by_name(obj, 'Catalog Description')
        full_description = self.__get_description_by_name(obj, 'Full Catalog Description' )

        ctx['descriptions'] = {
            'Catalog Description': {
                'explanation': 'The description pulled from the UCF Catalog that has been passed through a simple algorithm to remove the degree requirements.',
                'description': catalog_description.description if catalog_description is not None else None,
            },
            'Full Catalog Description': {
                'explanation': 'The full catalog description pulled from the UCF Catalog.',
                'description': full_description.description if full_description is not None else None,
            }
        }

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


class UsageReportView(LoginRequiredMixin, TitleContextMixin, TemplateView):
    template_name = 'dashboard/usage-report.html'
    title = 'Usage Report'
    heading = 'Usage Report'
    local = settings.LOCAL

    def create_blank_result(self, entry):
        """
        Returns a blank record for the results dictionary.
        """
        return {
            'first_name': entry['actor__first_name'],
            'last_name': entry['actor__last_name'],
            'descriptions_created': 0,
            'descriptions_updated': 0,
            'programs_job_created_updated': 0,
            'programs_highlights_created_updated': 0
        }


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        start_date = timezone.datetime.now() - timezone.timedelta(365)
        end_date = timezone.datetime.now()

        program_content_type = ContentType.objects.get_for_model(Program)
        program_description_content_type = ContentType.objects.get_for_model(ProgramDescription)

        descriptions_created = LogEntry.objects.filter(
            content_type=program_description_content_type,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            action=LogEntry.Action.CREATE
        ).values(
            'actor_id',
            'actor__first_name',
            'actor__last_name'
        ).exclude(
            actor=1
        ).annotate(
            action_count=Count('actor')
        ).order_by(
            'action_count'
        )

        descriptions_updated = LogEntry.objects.filter(
            content_type=program_description_content_type,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            action=LogEntry.Action.UPDATE
        ).values(
            'actor_id',
            'actor__first_name',
            'actor__last_name'
        ).exclude(
            actor=1
        ).annotate(
            action_count=Count('actor')
        ).order_by(
            'action_count'
        )

        programs_jobs_actions = LogEntry.objects.filter(
            content_type=program_content_type,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            action=LogEntry.Action.UPDATE
        ).filter(
            changes__icontains='jobs'
        ).values(
            'actor_id',
            'actor__first_name',
            'actor__last_name'
        ).exclude(
            actor=1
        ).annotate(
            action_count=Count('object_id', distinct=True)
        ).order_by(
            'action_count'
        )

        programs_highlights_actions = LogEntry.objects.filter(
            content_type=program_content_type,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            action=LogEntry.Action.UPDATE
        ).filter(
            changes__icontains="highlights"
        ).values(
            'actor_id',
            'actor__first_name',
            'actor__last_name'
        ).exclude(
            actor=1
        ).annotate(
            action_count=Count('object_id', distinct=True)
        ).order_by(
            'action_count'
        )

        results = {}

        for entry in [x for x in descriptions_created if x['actor_id'] is not None]:
            if entry['actor_id'] not in results.keys():
                results[entry['actor_id']] = self.create_blank_result(entry)

            results[entry['actor_id']]['descriptions_created'] = entry['action_count']


        for entry in [x for x in descriptions_updated if x['actor_id'] is not None]:
            if entry['actor_id'] not in results.keys():
                results[entry['actor_id']] = self.create_blank_result(entry)

            results[entry['actor_id']]['descriptions_updated'] = entry['action_count']


        for entry in [x for x in programs_jobs_actions if x['actor_id'] is not None]:
            if entry['actor_id'] not in results.keys():
                results[entry['actor_id']] = self.create_blank_result(entry)

            results[entry['actor_id']]['programs_jobs_actions'] = entry['action_count']


        for entry in [x for x in programs_highlights_actions if x['actor_id'] is not None]:
            if entry['actor_id'] not in results.keys():
                results[entry['actor_id']] = self.create_blank_result(entry)

            results[entry['actor_id']]['programs_highlights_actions'] = entry['action_count']


        ctx['results'] = results

        return ctx

class OpenJobListView(APIView):
    def get(self, request):
        # Parameters recieving
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))

        url = "https://jobs.ucf.edu/jobs/search"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')  # Specify the parser

        cards = soup.find_all(class_="job-search-results-card-title")

        # Base URL to remove
        base_url = "https://jobs.ucf.edu/jobs"

        jobs = []
        for card in cards:
            a_tag = card.find('a')
            if a_tag:
                href = a_tag.get('href')
                title = a_tag.get_text(strip=True)

                if href.startswith(base_url):
                    href = href[len(base_url):]

                jobs.append({'title': title, 'externalPath': href})

        # apply offset and limit to the jobs array
        jobs = jobs[offset: offset+limit]

        # Format the response
        response_data = {'jobPostings': jobs}
        return Response(response_data, status=status.HTTP_200_OK)
