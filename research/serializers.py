from rest_framework import serializers
from research.models import *
from teledata.serializers import StaffSerializer

class ResearcherEducationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ResearcherEducation

class ResearchWorkSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'title', 'publish_date', 'work_type', 'citation',)
        model = ResearchWork

class ResearcherSerializer(serializers.ModelSerializer):
    teledata_record = StaffSerializer(many=False, read_only=True)
    education = ResearcherEducationSerializer(many=True, read_only=True)
    works = serializers.HyperlinkedIdentityField(
        view_name='api.researcher.works.list',
        lookup_field='id'
    )
    works_count = serializers.SerializerMethodField(read_only=True)

    def get_works_count(self, researcher):
        return researcher.works.count()

    class Meta:
        fields = (
            'id',
            'orcid_id',
            'name_formatted_title',
            'name_formatted_no_title',
            'biography',
            'teledata_record',
            'education',
            'works',
            'works_count',
            'featured_works_count'
        )
        model = Researcher
