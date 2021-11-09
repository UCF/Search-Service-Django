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
    organization = OrganizationSerializer(many=False, read_only=True)
    college = CollegeSerializer(many=False, read_only=True)
    division = DivisionSerializer(many=False, read_only=True)
    department = DepartmentSerializer(many=False, read_only=True)

    class Meta:
        fields = [
            'ext_employee_id',
            'first_name',
            'last_name',
            'prefix',
            'department',
            'organization',
            'division',
            'college'
        ]
        model = Employee
