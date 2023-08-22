from django.conf.urls import url, include
from django.urls import reverse_lazy
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
        r'^manager/search/$',
        SearchView.as_view(template_name='search.html'),
        name='search'
    ),
    url(
        r'^user/current/$',
        CurrentUserView.as_view(),
        name='user.current'
    ),
    url(
        r'^settings/$',
        SettingsAPIView.as_view(),
        name='settings'
    )
]
