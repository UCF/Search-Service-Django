# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from teledata.models import *
from teledata.serializers import *

# Create your views here.
class BuildingListView(generics.ListAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer