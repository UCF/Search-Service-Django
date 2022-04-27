from django.conf.urls import url, include

from locations.views import *

urlpatterns = [
    # url(r'^$',
    #     CombinedTeledataSearchView.as_view(),
    #     name='api.teledata.search'
    #     ),
    # url(r'^buildings/$',
    #     BuildingListView.as_view(),
    #     name='api.teledata.buildings.list'
    #     ),
    # url(r'^departments/$',
    #     DepartmentListView.as_view(),
    #     name='api.teledata.departments.list'
    #     ),
    # url(r'^departments/(?P<id>\d+)/$',
    #     DepartmentDetailView.as_view(),
    #     name='api.teledata.departments.detail'
    #     ),
    # url(r'^organizations/$',
    #     OrganizationListView.as_view(),
    #     name='api.teledata.organizations.list'
    #     ),
    # url(r'^staff/$',
    #     StaffListView.as_view(),
    #     name='api.teledata.staff.list'
    #     ),
]
