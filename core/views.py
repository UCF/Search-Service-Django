# -*- coding: utf-8 -*-


from django.conf import settings

from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response

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

class CurrentUserView(APIView):
    def get(self, request, format=None, **kwargs):
        if self.request.user is None:
            return Response({
                'error': 'You must login to view this endpoint'
            }, status=403)
        
        return Response({
            'id': self.request.user.id,
            'username': self.request.user.username,
            'is_staff': self.request.user.is_staff,
            'is_superuser': self.request.user.is_superuser
        })

class SettingsAPIView(LoginRequiredMixin, APIView):
    def get(self, request, format=None, **kwargs):
        return Response({
            'ucf_news_api': settings.UCF_NEWS_API,
            'ucf_events_api': settings.UCF_EVENTS_API,
            'ucf_search_service_api': settings.UCF_SEARCH_SERVICE_API,
            'ucf_mediagraph_api_url': settings.UCF_MEDIAGRAPH_API_URL,
            'ucf_mediagraph_api_key': settings.UCF_MEDIAGRAPH_API_KEY,
            'ucf_mediagraph_org_id': settings.UCF_MEDIAGRAPH_ORG_ID
        })
