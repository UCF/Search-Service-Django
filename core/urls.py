from django.conf.urls import url, include
from django.urls import path
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from core.views import *

from teledata.views import *
from programs.views import *

urlpatterns = [
    url(
        r'^$',
        HomeView.as_view(),
        name='home'
    ),
    url(
        r'manager/dashboard/$',
        CommunicatorDashboard.as_view(),
        name='dashboard'
    ),
    url(
        r'manager/dashboard/usage/$',
        UsageReportView.as_view(),
        name='dashboard.usage'
    ),
    url(
        r'manager/dashboard/programs/$',
        ProgramListing.as_view(),
        name='dashboard.programs.list'
    ),
    url(
        r'manager/dashboard/programs/(?P<pk>\d+)/$',
        ProgramEditView.as_view(),
        name='dashboard.programs.edit'
    ),
    url(
        r'^manager/search/$',
        SearchView.as_view(template_name='search.html'),
        name='search'
    ),
    url(r'^api/v1/positions/$',
        OpenJobListView.as_view(),
        name='api.positions.list'
    ),
    url(
        r'^settings/$',
        SettingsAPIView.as_view(),
        name='settings'
    )
]
