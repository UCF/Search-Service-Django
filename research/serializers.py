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
    works = ResearchWorkSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            'id',
            'orcid_id',
            'biography',
            'teledata_record',
            'education',
            'works'
        )
        model = Researcher
