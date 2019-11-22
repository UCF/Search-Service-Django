from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class BackwardsCompatiblePagination(PageNumberPagination):
    def get_paginated_response(self, data):
        fields = OrderedDict()
        fields['count'] = self.page.paginator.count
        # Added for backwards compatibility
        fields['resultCount'] = self.page.paginator.count
        fields['next'] = self.get_next_link()
        fields['previous'] = self.get_previous_link()
        fields['results'] = data

        return Response(fields)
