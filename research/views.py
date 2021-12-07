from django.db.models import Count

from rest_framework import generics
from research.serializers import *

# Create your views here.
class ResearcherListView(generics.ListAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer

class ResearcherDetailView(generics.RetrieveAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer

class BookListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = BookSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return Book.objects.filter(researchers=researcher_id).order_by('-publish_date')

        return None

class ArticleListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = ArticleSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return Article.objects.filter(researchers=researcher_id).order_by('-article_year')

        return None

class BookChapterListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = BookChapterSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return BookChapter.objects.filter(researchers=researcher_id).order_by('-publish_date')

        return None

class ConferenceProceedingListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = ConferenceProceedingSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return ConferenceProceeding.objects.filter(researchers=researcher_id).order_by('-article_year')

        return None

class GrantListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = GrantSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return Grant.objects.filter(researchers=researcher_id).order_by('-start_date')

        return None

class HonorificAwardListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = HonorificAwardSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return HonorificAward.objects.filter(researchers=researcher_id).order_by('-award_received_year')

        return None

class PatentListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = PatentSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return Patent.objects.filter(researchers=researcher_id).order_by('-patent_date')

        return None

class ClinicalTrialListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = ClinicalTrialSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return ClinicalTrial.objects.filter(researchers=researcher_id).order_by('-start_date')

        return None

class ResearchTermListView(generics.ListAPIView):
    lookup_field = 'id'
    serializer_class = ResearchTermSerializer

    def get_queryset(self):
        researcher_id = self.kwargs['id'] if 'id' in list(self.kwargs.keys()) else None
        if researcher_id:
            return ResearchTerm.objects.annotate(
                researcher_count=Count('researchers')
            ).filter(
                researchers=researcher_id
            ).order_by('-researcher_count')
