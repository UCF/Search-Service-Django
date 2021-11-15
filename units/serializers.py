from rest_framework import serializers
from units.models import *

class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'ext_org_id',
            'name'
        ]
        model = Organization

class CollegeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'name'
        ]
        model = College

class DivisionSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'name'
        ]
        model = Division

class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [
            'ext_department_id',
            'name'
        ]
        model = Department

class EmployeeSerializer(serializers.ModelSerializer):
    organizations = OrganizationSerializer(many=True, read_only=True)
    colleges = CollegeSerializer(many=True, read_only=True)
    divisions = DivisionSerializer(many=True, read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        fields = [
            'ext_employee_id',
            'first_name',
            'last_name',
            'prefix',
            'departments',
            'organizations',
            'divisions',
            'colleges'
        ]
        model = Employee
