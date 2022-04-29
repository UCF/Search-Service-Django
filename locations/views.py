# -*- coding: utf-8 -*-


from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from locations.models import *
from locations.serializers import *
# from locations.filters import *

from rest_framework.filters import OrderingFilter


# Create your views here.

# TODO
