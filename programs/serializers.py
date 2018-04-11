from rest_framework import serializers
from programs.models import *


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


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = College


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class ProgramProfileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramProfileType


class ProgramProfileSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramProfile


class ParentProgramSerializer(serializers.ModelSerializer):
    level = serializers.StringRelatedField(many=False)
    career = serializers.StringRelatedField(many=False)
    degree = serializers.StringRelatedField(many=False)

    colleges = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='api.colleges.detail',
        lookup_field='id'
    )

    departments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='api.departments.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'name',
            'plan_code',
            'subplan_code',
            'catalog_url',
            'colleges',
            'departments',
            'level',
            'career',
            'degree'
        )
        model = Program


class ProgramSerializer(serializers.ModelSerializer):
    level = serializers.StringRelatedField(many=False)
    career = serializers.StringRelatedField(many=False)
    degree = serializers.StringRelatedField(many=False)

    colleges = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='api.colleges.detail',
        lookup_field='id'
    )

    departments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='api.departments.detail',
        lookup_field='id'
    )

    parent_program = ParentProgramSerializer(many=False, read_only=True)

    class Meta:
        fields = (
            'name',
            'plan_code',
            'subplan_code',
            'catalog_url',
            'colleges',
            'departments',
            'level',
            'career',
            'degree',
            'parent_program'
        )
        model = Program
