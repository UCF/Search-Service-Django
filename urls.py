"""src URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import RedirectView
import django_saml2_auth.views

import django_saml2_auth.views

urlpatterns = [
    url(r'^api/v1/teledata/',
        include('teledata.urls')
        ),
    url(r'^api/v1/images/',
        include('images.urls')
        ),
    url(r'^api/v1/',
        include('programs.urls')
        ),
    url(r'^api/v1/research/',
        include('research.urls')
        ),
    url(r'^api-auth/',
        include('rest_framework.urls')
        ),
    url(r'^admin/',
        admin.site.urls
        ),
    url(
        r'^favicon.ico$',
        RedirectView.as_view(url='/static/favicon.ico'),
        name='favicon'
        ),
    url(
        r'^manager/$',
        RedirectView.as_view(pattern_name='login'), name='manager'
    ),
    url(
        r'^manager/login/$',
        LoginView.as_view(template_name='login.html'), name='login'
    ),
    url(
        r'^manager/logout/$',
        LogoutView.as_view(template_name='logout.html'), name='logout'
    ),
    url(r'^',
        include('core.urls')
    )
]

if settings.USE_SAML:
    urlpatterns.insert(
        0,
        url(r'^sso/',
            include('django_saml2_auth.urls')
        )
    )
    urlpatterns.insert(
        1,
        url(r'^accounts/login/$',
            django_saml2_auth.views.signin
        )
    )
    urlpatterns.insert(
        2,
        url(r'^admin/login/$',
            django_saml2_auth.views.signin
        )
    )
