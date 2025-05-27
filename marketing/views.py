from rest_framework import generics
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from marketing.models import *
from marketing.serializers import *
from marketing.filters import QuoteFilter
from marketing.parsers import MultiPartJSONParser

from programs.models import Program

# Create your views here.
class QuoteListView(generics.ListAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    filter_class = QuoteFilter

class QuoteCreateView(generics.CreateAPIView):
    serializer_class = QuoteSerializer

    def create(self, request, *args, **kwargs):
        program_id = request.headers.get('Program-ID')
        quote_serializer = self.get_serializer(data=request.data)
        quote_serializer.is_valid(raise_exception=True)
        quote = quote_serializer.save(author=request.user)

        try:
            program = Program.objects.get(id=program_id)
            program.quotes.add(quote)
            return Response({"message": "Quote attached successfully"})
        except Program.DoesNotExist:
            return Response({"message": "Program not found"})

class QuoteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quote.objects.all()
    lookup_field = 'id'
    serializer_class = QuoteSerializer
    parser_classes = (MultiPartJSONParser,JSONParser,)

    def patch(self, request, *args, **kwargs):
        program_id = request.headers.get('Program-ID')
        attribute = request.headers.get('Attr-Quote')
        program = Program.objects.get(id=program_id)
        quote = self.get_object()

        if attribute == 'detachQuote':
            try:

                if quote in program.quotes.all():
                    program.quotes.remove(quote)
                    return Response({"message": "Quote detached successfully"})
                else:
                    return Response({"error": "Quote was not attached to this program"})

            except Program.DoesNotExist:
                return Response({"error": "Program not found"})

        if attribute == 'attachQuote':
            try:

                if quote not in program.quotes.all():
                    program.quotes.add(quote)
                    return Response({"message": "Quote attached successfully"})
                else:
                    return Response({"error": "Quote already attached to this program"})

            except Program.DoesNotExist:
                return Response({"error": "Program not found"})


