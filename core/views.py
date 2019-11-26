# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic.base import TemplateView

# Create your views here.
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['title'] = 'UCF Search Service'

        return context

class TeledataDocsView(TemplateView):
    template_name = 'redoc.html'

    def get_context_data(self, **kwargs):
        context = super(TeledataDocsView, self).get_context_data(**kwargs)
        context['schema_url'] = 'core.openapi.teledata'

        return context

class ProgramsDocsView(TemplateView):
    template_name = 'redoc.html'

    def get_context_data(self, **kwargs):
        context = super(ProgramsDocsView, self).get_context_data(**kwargs)
        context['schema_url'] = 'core.openapi.programs'

        return context
