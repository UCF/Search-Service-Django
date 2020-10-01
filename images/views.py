# -*- coding: utf-8 -*-


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


class ImageSearchView(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSearchSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['tags__name', 'tags__synonyms__name', 'caption', 'location']
    ordering_fields = ['score', 'source_created', 'source_modified', 'photo_taken']
    ordering = ['-score', '-photo_taken']

    def get_ordering(self):
        if self.request.GET.get('search') is None:
            # There is no score because the query isn't run;
            # remove ordering by score
            return ['-photo_taken']
        return self.ordering

    def get_queryset(self):
        if self.request.GET.get('search') is not None:
            return Image.objects.search(self.request.GET.get('search'))
        else:
            return Image.objects.none()
