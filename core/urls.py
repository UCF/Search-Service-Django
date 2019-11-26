from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from core.views import *

urlpatterns = [
    url(
        r'^$',
        HomeView.as_view(),
        name='home'
    )
]
