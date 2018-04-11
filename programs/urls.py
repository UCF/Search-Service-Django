from django.conf.urls import url, include

from programs.views import *

urlpatterns = [
    url(r'^programs/$', ProgramListView.as_view(), name='api.programs.list'),
    url(r'^colleges/$', CollegeListView.as_view(), name='api.colleges.list'),
    url(r'^colleges/(?P<id>\d+)/$', CollegeDetailView.as_view(), name='api.colleges.detail'),
    url(r'^departments/$', DepartmentListView.as_view(), name='api.departments.list'),
    url(r'^departments/(?P<id>\d+)/$', DepartmentDetailView.as_view(), name='api.departments.detail')
]
