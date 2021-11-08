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
            'id',
            'name',
            'phone',
            'fax',
            'url',
            'room',
            'import_id'
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


class StaffContactSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'email',
            'phone'
        ]
        model = Staff

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


class CombinedTeledataSerializer(serializers.ModelSerializer):
    score = serializers.DecimalField(
        20,
        10
    )

    class Meta:
        fields = (
            'score',
            'id',
            'alpha',
            'name',
            'first_name',
            'last_name',
            'sort_name',
            'email',
            'phone',
            'fax',
            'postal',
            'job_position',
            'department',
            'dept_id',
            'organization',
            'org_id',
            'building',
            'bldg_id',
            'room',
            'from_table',
            'active'
        )
        model = CombinedTeledata
