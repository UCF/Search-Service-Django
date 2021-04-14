# -*- coding: utf-8 -*-
from django.conf import settings

from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from jsonview.views import JsonView
import requests
from requests.auth import HTTPBasicAuth

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

class KeywordSearchView(LoginRequiredMixin, TitleContextMixin, TemplateView):
    template_name = 'keyword-search.html'
    title = 'UCF Keyword Search'
    heading = 'UCF Search Service'
    local = settings.LOCAL

    def get_context_data(self, **kwargs):
        context = super(KeywordSearchView, self).get_context_data(**kwargs)

        if not settings.MICROSOFT_AZURE_API_KEY or not settings.BING_SEARCH_API_BASE:
            context['search_error'] = "Azure API Key and Bing Search API Base Url are required settings."
            return context

        q = self.request.GET.get('q', None)
        if not q:
            return context

        context['q'] = q
        q = f"\"{q}\""

        headers = {
            "Ocp-Apim-Subscription-Key": settings.MICROSOFT_AZURE_API_KEY
        }

        params = {
            "q": q + " site:ucf.edu",
            "textDecorations": True,
            "textFormat": "HTML"
        }

        response = requests.get(settings.BING_SEARCH_API_BASE, headers=headers, params=params)
        response.raise_for_status()
        context['bing_results'] = response.json()

        return context

    def post(self, request, *args, **kwargs):
        q = request.POST.get('q', None)
        email = request.POST.get('report-email', None)
        jenkins_path = settings.JENKINS_CRAWLER_JOB
        crumb_path = f'{settings.JENKINS_BASE_URL}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'
        username = settings.JENKINS_USERNAME
        token = settings.JENKINS_TOKEN

        auth = HTTPBasicAuth(username, token)

        crumb = requests.get(crumb_path, verify=False, auth=auth)
        token = crumb.text[14:]

        if q and email and jenkins_path and token:
            # Send jenkins a request to run the report
            params = {
                'KEYWORDS': q,
                'REPORT_EMAIL': email
            }

            headers = {
                'Jenkins-Crumb': token
            }

            response = requests.post(
                f"{jenkins_path}/buildWithParameters",
                data=params,
                verify=False,
                auth=auth,
                headers=headers
            )

            print(response.text)

            if response.ok:
                self.get(request, *args, **kwargs)
            else:
                self.get(request, *args, **kwargs)
        else:
            # Throw an error
            print("There was an error")

        return self.get(request)

class SettingsAPIView(APIView):
    def get(request, format=None, **kwargs):
        return Response({
            'ucf_news_api': settings.UCF_NEWS_API,
            'ucf_events_api': settings.UCF_EVENTS_API,
            'ucf_search_service_api': settings.UCF_SEARCH_SERVICE_API
        })
