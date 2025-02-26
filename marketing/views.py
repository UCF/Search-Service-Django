from rest_framework import generics
from rest_framework.parsers import JSONParser

from marketing.models import *
from marketing.serializers import *
from marketing.parsers import MultiPartJSONParser

# Create your views here.
class QuoteListView(generics.ListAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer

class QuoteCreateView(generics.CreateAPIView):
    serializer_class = QuoteSerializer

class QuoteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quote.objects.all()
    lookup_field = 'id'
    serializer_class = QuoteSerializer
    parser_classes = (MultiPartJSONParser,JSONParser,)

