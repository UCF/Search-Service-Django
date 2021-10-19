from rest_framework import serializers
from research.models import *
from teledata.serializers import StaffSerializer

class ResearcherEducationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ResearcherEducation

class BookSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Book

class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Article

class BookChapterSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = BookChapter

class ConferenceProceedingSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = ConferenceProceeding

class GrantSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Grant

class HonorificAwardSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = HonorificAward

class PatentSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Patent

class ClinicalTrialSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = ClinicalTrial

class ResearcherSerializer(serializers.ModelSerializer):
    teledata_record = StaffSerializer(many=False, read_only=True)
    education = ResearcherEducationSerializer(many=True, read_only=True)
    books = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.books.list',
        lookup_field='id'
    )
    articles = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.articles.list',
        lookup_field='id'
    )
    book_chapters = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.bookchapters.list',
        lookup_field='id'
    )
    conference_proceedings = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.proceedings.list',
        lookup_field='id'
    )
    grants = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.grants.list',
        lookup_field='id'
    )
    honorific_awards = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.awards.list',
        lookup_field='id'
    )
    patents = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.patents.list',
        lookup_field='id'
    )
    clinical_trials = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.trials.list',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'id',
            'orcid_id',
            'name_formatted_title',
            'name_formatted_no_title',
            'biography',
            'teledata_record',
            'education',
            'books',
            'articles',
            'book_chapters',
            'conference_proceedings',
            'grants',
            'honorific_awards',
            'patents',
            'clinical_trials'
        )
        model = Researcher
