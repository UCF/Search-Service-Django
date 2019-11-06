from django.conf.urls import url, include

from teledata.views import *

urlpatterns = [
    url(r'^buildings/$',
        BuildingListView.as_view(),
        name='api.buildings.list'
        ),
    url(r'^departments/$',
        DepartmentListView.as_view(),
        name='api.departments.list'
        ),
    url(r'^departments/(?P<id>\d+)/$',
        DepartmentDetailView.as_view(),
        name='api.teledata.departments.detail'
        ),
    url(r'^organizations/$',
        OrganizationListView.as_view(),
        name='api.organizations.list'
        ),
    url(r'^staff/$',
        StaffListView.as_view(),
        name='api.staff.list'
        ),
]
