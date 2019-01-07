from rest_framework import serializers
from rest_framework.reverse import reverse
from programs.models import *

from django.db import IntegrityError


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
    update_url = serializers.HyperlinkedIdentityField(
        view_name='api.colleges.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'full_name',
            'short_name',
            'college_url',
            'profile_url',
            'update_url'
        )
        model = College


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = College


class DepartmentLinkSerializer(serializers.ModelSerializer):
    update_url = serializers.HyperlinkedIdentityField(
        view_name='api.departments.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'full_name',
            'department_url',
            'school',
            'update_url'
        )
        model = Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class ProgramProfileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramProfileType


class ProgramProfileLinkedSerializer(serializers.ModelSerializer):
    profile_type = ProgramProfileTypeSerializer(
        many=False,
        read_only=True
    )

    update_url = serializers.HyperlinkedIdentityField(
        view_name='api.profiles.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'profile_type',
            'url',
            'primary',
            'program',
            'update_url'
        )
        model = ProgramProfile

class ProgramProfileSerializer(serializers.ModelSerializer):
    profile_type = ProgramProfileTypeSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        fields = ('profile_type', 'url', 'primary', 'program')
        model = ProgramProfile


class ProgramProfileWriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = ProgramProfile

class ProgramDescriptionTypeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = ProgramDescriptionType


class ProgramDescriptionLinkedSerializer(serializers.ModelSerializer):
    description_type = ProgramDescriptionTypeSerializer(
        many=False,
        read_only=True
    )

    update_url = serializers.HyperlinkedIdentityField(
        view_name='api.descriptions.detail',
        lookup_field='id'
    )

    class Meta:
        fields = ('id', 'description_type', 'description', 'primary', 'program', 'update_url')
        model = ProgramDescription


class ProgramDescriptionSerializer(serializers.ModelSerializer):
    description_type = ProgramDescriptionTypeSerializer(
        many=False,
        read_only=True
    )

    program = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True
    )

    class Meta:
        fields = ('id', 'description_type', 'description', 'primary', 'program')
        model = ProgramDescription


class ProgramDescriptionWriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
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

    descriptions = ProgramDescriptionLinkedSerializer(many=True, read_only=False)
    profiles = ProgramProfileLinkedSerializer(many=True, read_only=False)

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
            'id',
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
            'subplans',
            'resident_tuition',
            'nonresident_tuition',
            'tuition_type'
        )
        model = Program
