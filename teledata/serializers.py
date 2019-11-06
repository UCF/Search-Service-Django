from rest_framework import serializers
from teledata.models import *
import warnings

from django.db import IntegrityError

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Building


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Organization


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Staff
