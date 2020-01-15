# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter

from images.models import *
from images.serializers import *


class ImageListView(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class ImageDetailView(generics.RetrieveAPIView):
    queryset = Image.objects.all()
    lookup_field = 'id'
    serializer_class = ImageSerializer


class ImageSearchView(ImageListView):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['filename', 'tags__name', 'tags__synonyms__name', 'caption', 'location']
    ordering_fields = ['source_created', 'source_modified', 'photo_taken']
    ordering = ['-photo_taken']
