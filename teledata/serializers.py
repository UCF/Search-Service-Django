from rest_framework import serializers
from teledata.models import *
import warnings

from django.db import IntegrityError

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Building


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Organization


class OrganizationBriefSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'name',
            'phone',
            'fax',
            'url',
            'room'
        )
        model = Organization


class DepartmentSerializer(serializers.ModelSerializer):
    bldg = BuildingSerializer(
        many=False,
        read_only=True
    )

    org = OrganizationBriefSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = Department


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Staff
