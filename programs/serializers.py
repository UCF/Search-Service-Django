from rest_framework import serializers
from programs.models import *


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career


class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department


class ProgramProfileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramProfileType


class ProgramProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramProfile


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
