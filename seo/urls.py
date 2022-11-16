from django.conf.urls import url

from .views import *

urlpatterns = [
    url(
        r'patterns/$',
        AutoAnchorListView.as_view(),
        name='api.seo.autoanchors'
    ),
    url(
        r'backlinks/$',
        BackLinkView.as_view(),
        name='api.seo.backlinks'
    )
]
