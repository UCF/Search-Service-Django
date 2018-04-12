from rest_framework import serializers
from rest_framework.reverse import reverse
from programs.models import *


# Custom Serializers
class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Level


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Career


class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Degree


class CollegeLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api.colleges.detail',
        lookup_field='id'
    )

    class Meta:
        fields = ('full_name', 'url')
        model = College


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = College

class DepartmentLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api.departments.detail',
        lookup_field='id'
    )

    class Meta:
        fields = ('full_name', 'url')
        model = Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class ProgramProfileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramProfileType


class ProgramProfileSerializer(serializers.ModelSerializer):
    profile_type = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        fields = 'profile_type, url, primary'
        model = ProgramProfile


class ProgramDescriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramDescriptionType

class ProgramDescriptionSerializer(serializers.ModelSerializer):
    profile_type = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        fields = 'profile_type, description, primary'
        model = ProgramDescription

class RelatedProgramSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api.programs.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'name',
            'online',
            'url'
        )
        model = Program


class ProgramSerializer(serializers.ModelSerializer):
    level = serializers.StringRelatedField(many=False)
    career = serializers.StringRelatedField(many=False)
    degree = serializers.StringRelatedField(many=False)

    descriptions = ProgramDescriptionSerializer(many=True, read_only=True)
    profiles = ProgramProfileSerializer(many=True, read_only=True)

    colleges = CollegeLinkSerializer(
        many=True,
        read_only=True
    )

    departments = DepartmentLinkSerializer(
        many=True,
        read_only=True
    )

    parent_program = RelatedProgramSerializer(many=False, read_only=True)
    subplans = RelatedProgramSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            'name',
            'descriptions',
            'online',
            'has_online',
            'profiles',
            'plan_code',
            'subplan_code',
            'catalog_url',
            'colleges',
            'departments',
            'level',
            'career',
            'degree',
            'parent_program',
            'subplans'
        )
        model = Program
