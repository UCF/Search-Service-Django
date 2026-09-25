from django_filters import rest_framework as filters

from locations.models import Location


class LocationFilter(filters.FilterSet):
    # Text filters ignore case explicitly, so they behave the same on
    # MySQL and PostgreSQL.
    object_type = filters.CharFilter(lookup_expr='iexact')
    data_source = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = Location
        fields = ['object_type', 'data_source', 'visible', 'private', 'is_verified']
