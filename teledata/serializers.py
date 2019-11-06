from rest_framework import serializers
from teledata.models import *
import warnings

from django.db import IntegrityError

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Building


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


class OrganizationSerializer(serializers.ModelSerializer):
    bldg = BuildingSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = Organization


class DepartmentLinkSerializer(serializers.ModelSerializer):
    detail_url = serializers.HyperlinkedIdentityField(
        view_name='api.teledata.departments.detail',
        lookup_field='id'
    )
    
    class Meta:
        fields = (
            'id',
            'name',
            'detail_url'
        )
        model = Department    


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
    dept = DepartmentLinkSerializer(
        many=False,
        read_only=True
    )

    bldg = BuildingSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = Staff
