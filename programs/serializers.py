from rest_framework import serializers
from rest_framework.reverse import reverse
from programs.models import *
import warnings

from django.db import IntegrityError
from drf_dynamic_fields import DynamicFieldsMixin

class DynamicFieldSetMixin(DynamicFieldsMixin):
    """
    Expands the functionality of the Dynamic Fields Mixin
    """
    def __init__(self, *args, **kwargs):
        super(DynamicFieldSetMixin, self).__init__(*args, **kwargs)

        if hasattr(self.Meta, "fieldsets"):
            self.fieldsets = self.Meta.fieldsets
        else:
            self.fieldsets = None

    @property
    def fields(self):
        # Do initial fields logic
        fields = super(DynamicFieldSetMixin, self).fields

        # Check for request object in context
        try:
            request = self.context['request']
        except KeyError:
            warnings.warn('Context does not have access to request')
            return fields

        # Check for query_params within GET param
        params = getattr(
            request, 'query_params', getattr(request, 'GET', None)
        )
        if params is None:
            warnings.warn('Request object does not contain query paramters')

        # Get fieldset
        try:
            fieldset = params.get('fieldset', None)
        except AttributeError:
            fieldset = None
            return fields


        if self.fieldsets and fieldset in self.fieldsets:
            existing = set(fields.keys())
            allowed = self.fieldsets[fieldset]

            for field in existing:

                if field not in allowed:
                    fields.pop(field, None)

        return fields


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
            'id',
            'name',
            'online',
            'url'
        )
        model = Program


class ProgramSerializer(DynamicFieldSetMixin, serializers.ModelSerializer):
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
        fieldsets = (
            {"simple": "name,plan_code,subplan_code"}
        )
        model = Program

class CollegeOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = CollegeOverride

class TuitionOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = TuitionOverride
