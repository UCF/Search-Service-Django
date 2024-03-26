import django_filters
from django import forms
from django.conf import settings
from django.db.models import Count

from programs.models import College

class ProgramListFilterSet(django_filters.FilterSet):
    missing_choices = [
        ('', ''),
        ('Description Missing', 'missing'),
        ('Custom Description Missing', 'missing_custom'),
        ('Career Paths Missing', 'missing_jobs')
    ]

    colleges_choices = College.objects.values_list('id', 'full_name')

    name = django_filters.CharFilter(lookup_expr='icontains')
    colleges = django_filters.MultipleChoiceFilter(
        field_name='colleges',
        lookup_expr='in',
        choices=colleges_choices,
        widget=forms.CheckboxSelectMultiple({
            'class': 'list-unstyled'
        })
    )
    missing = django_filters.CharFilter(
        method='missing_descriptions'
    )

    order = django_filters.OrderingFilter(
        fields = (
            ('name', 'name'),
            ('modified', 'modified')
        ),
        field_labels = {
            'name': 'Name',
            'modified': 'Last Modified',
        }
    )


    def __init__(self, data, *args, **kwargs):
        data = data.copy()
        super().__init__(data, *args, **kwargs)

    def missing_descriptions(self, queryset, name, value):
        """
        Filter for displaying missing descriptions
        """
        if value == 'missing':
            return queryset.annotate(
                num_descriptions=Count('descriptions')
            ).filter(num_descriptions=0)
        elif value == 'missing_custom':
            programs_with_custom_descriptions = queryset.filter(
                descriptions__description_type=settings.CUSTOM_DESCRIPTION_TYPE_ID
            )

            return queryset.exclude(
                id__in=programs_with_custom_descriptions
            )
        elif value == 'missing_jobs':
            return queryset.annotate(
                num_jobs=Count('jobs')
            ).filter(num_jobs=0)

        return queryset
