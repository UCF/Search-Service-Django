from rest_framework import generics
from research.serializers import *

# Create your views here.
class ResearcherListView(generics.ListAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer

class ResearchWorkListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = ResearchWorkSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return ResearchWork.objects.filter(researcher__id=researcher_id)

        return None
