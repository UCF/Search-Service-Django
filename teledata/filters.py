import django_filters
from django_filters import rest_framework as filters

from teledata.models import CombinedTeledata


# WIP:
class CombinedTeledataFilter(django_filters.FilterSet):
    search = filters.CharFilter(name='name', lookup_expr='icontains')

    class Meta:
        model = CombinedTeledata
        fields = ('__all__')
