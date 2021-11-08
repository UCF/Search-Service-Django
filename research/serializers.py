from rest_framework import serializers
from research.models import *
from teledata.serializers import StaffContactSerializer

class ResearcherEducationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ResearcherEducation

class BookSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_book_id',
            'isbn',
            'book_title',
            'bisac',
            'publisher_name',
            'publish_date',
            'researchers',
            'simple_citation_html'
        ]
        model = Book

class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_article_id',
            'article_title',
            'journal_name',
            'article_year',
            'journal_volume',
            'journal_issue',
            'first_page',
            'last_page',
            'researchers',
            'simple_citation_html'
        ]
        model = Article

class BookChapterSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_book_id',
            'isbn',
            'book_title',
            'chapter_title',
            'bisac',
            'publisher_name',
            'publish_year',
            'publish_date',
            'researchers',
            'simple_citation_html'
        ]
        model = BookChapter

class ConferenceProceedingSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_article_id',
            'proceeding_title',
            'journal_name',
            'article_year',
            'journal_volume',
            'journal_issue',
            'first_page',
            'last_page',
            'researchers',
            'simple_citation_html'
        ]
        model = ConferenceProceeding

class GrantSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_grant_id',
            'agency_name',
            'grant_name',
            'duration_years',
            'start_date',
            'end_date',
            'full_name',
            'total_dollars',
            'is_research',
            'principle_investigator',
            'researchers',
            'simple_citation_html'
        ]
        model = Grant

class HonorificAwardSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'aa_award_id',
            'governing_society_name',
            'award_name',
            'award_received_name',
            'award_received_year',
            'researchers',
            'simple_citation_html'
        ]
        model = HonorificAward

class PatentSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'patent_id',
            'patent_title',
            'patent_type',
            'patent_kind',
            'patent_date',
            'country',
            'claims',
            'abstract',
            'researchers',
            'simple_citation_html'
        ]
        model = Patent

class ClinicalTrialSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'nct_id',
            'title',
            'start_date',
            'completion_date',
            'study_type',
            'sponsor',
            'allocation',
            'phase',
            'recruitment_status',
            'investigators',
            'researchers',
            'simple_citation_html'
        ]
        model = ClinicalTrial

class ResearcherSerializer(serializers.ModelSerializer):
    teledata_record = StaffContactSerializer(many=False, read_only=True)
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
