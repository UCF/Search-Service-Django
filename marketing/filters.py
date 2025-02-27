from django.db.models import Q

import django_filters
from django_filters import rest_framework as filters

from marketing.models import Quote

class QuoteFilter(django_filters.FilterSet):
    search = filters.CharFilter(method='custom_quote_search', label='Search')
    tags = filters.CharFilter(method='custom_tag_search', label='Tags')

    class Meta:
        model = Quote
        fields = (
            'search',
            'tags',
        )

    def custom_quote_search(self, queryset, name, value):
        return queryset.filter(
            Q(quote_text__icontains=value) |
            Q(source__icontains=value) |
            Q(titles__icontains=value)
        )

    def custom_tag_search(self, queryset, name, value):
        tag_values = value.split(',')

        return queryset.filter(
            tags__name__in=tag_values
        )
