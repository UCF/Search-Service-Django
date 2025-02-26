from django.conf.urls import url, include

from marketing.views import *

urlpatterns = [
    url(r'^quotes/$',
        QuoteListView.as_view(),
        name='api.marketing.quotes.list'
    ),
    url(r'^quotes/(?P<id>\d+)/$',
        QuoteRetrieveUpdateDestroyView.as_view(),
        name='api.marketing.quotes.single'
    ),
    url(r'^quotes/create/$',
        QuoteCreateView.as_view(),
        name='api.marketing.quotes.create'
    ),
]
