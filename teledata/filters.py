import django_filters
from django_filters import rest_framework as filters

from teledata.models import CombinedTeledata


class CombinedTeledataFilter(django_filters.FilterSet):
    use = filters.CharFilter(name='from_table')

    class Meta:
        model = CombinedTeledata
        fields = ('__all__')
