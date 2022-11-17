from django.conf.urls import url

from .views import *

urlpatterns = [
    url(
        r'internal-links/$',
        InternalLinkListView.as_view(),
        name='api.seo.autoanchors'
    )
]
