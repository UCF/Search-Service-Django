from django.conf.urls import url

from research.views import *

urlpatterns = [
    url(r'^researchers/$',
        ResearcherListView.as_view(),
        name='api.researchers.list'
    ),
    url(r'^researchers/(?P<id>\d+)/books/$',
        BookListView.as_view(),
        name='api.researcher.books.list'
    ),
    url(r'^researchers/(?P<id>\d+)/articles/$',
        ArticleListView.as_view(),
        name='api.researcher.articles.list'
    ),
    url(r'^researchers/(?P<id>\d+)/bookchapters/$',
        BookChapterListView.as_view(),
        name='api.researcher.bookchapters.list'
    ),
    url(r'^researchers/(?P<id>\d+)/proceedings/$',
        ConferenceProceedingListView.as_view(),
        name='api.researcher.proceedings.list'
    ),
    url(r'^researchers/(?P<id>\d+)/grants/$',
        GrantListView.as_view(),
        name='api.researcher.grants.list'
    ),
    url(r'^researchers/(?P<id>\d+)/awards/$',
        HonorificAwardListView.as_view(),
        name='api.researcher.awards.list'
    ),
    url(r'^researchers/(?P<id>\d+)/patents/$',
        PatentListView.as_view(),
        name='api.researcher.patents.list'
    ),
    url(r'^researchers/(?P<id>\d+)/trials/$',
        ClinicalTrialListView.as_view(),
        name='api.researcher.trials.list'
    )
]
