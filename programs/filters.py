import django_filters
from django_filters import rest_framework as filters

from programs.models import *


class ProgramFilter(django_filters.FilterSet):
    search = filters.CharFilter(name='name', lookup_expr='icontains')


    class Meta:
        model = Program
        fields = (
            'search',
            'plan_code',
            'subplan_code',
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
