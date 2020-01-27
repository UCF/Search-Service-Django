# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

from django.shortcuts import render
from django.views.generic.base import TemplateView

class TitleContextMixin(object):
    """
    Mixin for setting title and heading
    """
    def get_context_data(self, **kwargs):
        context = super(TitleContextMixin, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['heading'] = self.heading
        context['newsApi'] = self.newsApi
        context['searchServiceApi'] = self.searchServiceApi

        return context

# Create your views here.
class HomeView(TitleContextMixin, TemplateView):
    template_name = 'home.html'
    title = ''
    heading = 'UCF Search Service'

class SearchView(TitleContextMixin, TemplateView):
    template_name = 'search.html'
    title = ''
    heading = 'UCF Search Service'
    newsApi = settings.UCF_NEWS_API
    searchServiceApi = settings.UCF_SEARCH_SERVICE_API
