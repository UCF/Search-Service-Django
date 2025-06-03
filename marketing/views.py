from rest_framework import generics
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status

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
        program_id = request.data.get('program_id')
        quote_serializer = self.get_serializer(data=request.data)
        quote_serializer.is_valid(raise_exception=True)
        quote = quote_serializer.save(author=request.user)

        try:
            program = Program.objects.get(id=program_id)
            program.quotes.add(quote)
            return Response(
                {"message": "Quote created and attached successfully"},
                status=status.HTTP_201_CREATED
            )
        except Program.DoesNotExist:
            return Response(
                {"error": "Program not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

class QuoteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quote.objects.all()
    lookup_field = 'id'
    serializer_class = QuoteSerializer
    parser_classes = (MultiPartJSONParser,JSONParser,)

    def patch(self, request, *args, **kwargs):
        program_id = request.data.get('program_id')
        attribute = request.data.get('quote_attribute')
        program = Program.objects.get(id=program_id)
        quote = self.get_object()

        if attribute == 'detachQuote':
            try:

                if quote in program.quotes.all():
                    program.quotes.remove(quote)
                    return Response(
                    {"message": "Quote detached successfully"},
                    status=status.HTTP_200_OK
                )
                else:
                    return Response(
                {"error": "Program not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

            except Program.DoesNotExist:
                return Response(
                {"error": "Program not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attribute == 'attachQuote':
            try:

                if quote not in program.quotes.all():
                    program.quotes.add(quote)
                    return Response({"message": "Quote attached successfully"},
                    status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Quote already attached to this program"},
                status=status.HTTP_409_CONFLICT)

            except Program.DoesNotExist:
                return Response({"error": "Program not found"},status=status.HTTP_400_BAD_REQUEST)


