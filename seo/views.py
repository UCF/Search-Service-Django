from rest_framework import views, status, generics
from rest_framework.response import Response

from .models import AutoAnchor
from .serializers import FoundPatternsSerializer, AutoAnchorSerializer

# Create your views here.
class AutoAnchorListView(generics.ListAPIView):
    model = AutoAnchor
    queryset = AutoAnchor.objects.all()
    serializer_class = AutoAnchorSerializer

class BackLinkView(views.APIView):
    def post(self, request):
        content = request.data.get('content')

        patterns = AutoAnchor.objects.find_in_text(content)
        matches = patterns.count() > 0
        serializer = FoundPatternsSerializer({
            'count': patterns.count(),
            'matches': matches,
            'patterns': patterns
        }, many=False)

        return Response(serializer.data, status.HTTP_200_OK)
