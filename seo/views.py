from rest_framework import views, status, generics
from rest_framework.response import Response

from .models import InternalLink
from .serializers import InternalLinkSerializer

# Create your views here.
class InternalLinkListView(generics.ListAPIView):
    model = InternalLink
    queryset = InternalLink.objects.all()
    serializer_class = InternalLinkSerializer

