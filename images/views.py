# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from rest_framework import generics

from images.models import *
from images.serializers import *
from images.filters import *


class ImageListView(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class ImageDetailView(generics.RetrieveAPIView):
    queryset = Image.objects.all()
    lookup_field = 'id'
    serializer_class = ImageSerializer


class ImageSearchView(ImageListView):
    filter_class = ImageFilter
