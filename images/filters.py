import django_filters
from django_filters import rest_framework as filters

from images.models import *


# TODO
class ImageFilter(django_filters.FilterSet):
    class Meta:
        model = Image
        fields = (
            'id',
            'filename'
        )
