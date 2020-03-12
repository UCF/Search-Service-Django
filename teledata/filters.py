import django_filters
from django_filters import rest_framework as filters

from teledata.models import Department, CombinedTeledata


class DepartmentFilter(django_filters.FilterSet):
    class Meta:
        model = Department
        fields = (
            'org__import_id',
        )


class CombinedTeledataFilter(django_filters.FilterSet):
    use = filters.CharFilter(name='from_table')

    class Meta:
        model = CombinedTeledata
        fields = (
            'pkid',
            'id',
            'alpha',
            'name',
            'use',
            'active'
        )
