from rest_framework import generics
from research.serializers import *

# Create your views here.
class ResearcherListView(generics.ListAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
