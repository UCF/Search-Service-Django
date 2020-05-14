import django_filters
from django_filters import rest_framework as filters

from programs.models import *


class ProgramFilter(django_filters.FilterSet):
    search = filters.CharFilter(name='name', lookup_expr='icontains')
    subplan_code__isnull = filters.BooleanFilter(name='subplan_code', lookup_expr='isnull')

    class Meta:
        model = Program
        fields = (
            'search',
            'valid',
            'active',
            'plan_code',
            'subplan_code',
            'subplan_code__isnull',
            'online',
            'colleges',
            'departments',
            'level',
            'career',
            'degree',
            'parent_program'
        )


class CollegeFilter(django_filters.FilterSet):
    search = filters.CharFilter(name='full_name', lookup_expr='icontains')

    class Meta:
        model = College
        fields = (
            'search',
            'short_name'
        )


class DepartmentFilter(django_filters.FilterSet):
    search = filters.CharFilter(name='full_name', lookup_expr='icontains')

    class Meta:
        model = Department
        fields = (
            'search',
            'school'
        )

class TuitionOverrideFilter(django_filters.FilterSet):

    class Meta:
        model = TuitionOverride
        fields = (
            'tuition_code',
            'plan_code',
            'subplan_code'
        )
