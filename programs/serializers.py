from re import L
from rest_framework import serializers
from rest_framework.reverse import reverse
from programs.models import *
import warnings

from django.db import IntegrityError
from django.db.models import Max, Avg, Sum
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
            warnings.warn('Request object does not contain query parameters')

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
            'name',
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
            'name',
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


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('__all__')
        model = AcademicYear


class CIPSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'name',
            'description',
            'version',
            'code',
            'area',
            'subarea',
            'precise'
        )
        model = CIP


class CIPSerializer(serializers.ModelSerializer):
    area_detail = serializers.SerializerMethodField()
    subarea_detail = serializers.SerializerMethodField()
    precise_detail = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'name',
            'description',
            'version',
            'code',
            'area',
            'subarea',
            'precise',
            'area_detail',
            'subarea_detail',
            'precise_detail'
        )
        model = CIP

    def get_area_detail(self, obj):
        try:
            cip = CIP.objects.get(area=obj.area, subarea=0, precise=0, version=obj.version)
        except:
            return None

        if cip == obj:
            return None

        ser = CIPSimpleSerializer(cip)
        return ser.data

    def get_subarea_detail(self, obj):
        try:
            cip = CIP.objects.get(area=obj.area, subarea=obj.subarea, precise=0, version=obj.version)
        except:
            return None

        if cip == obj:
            return None

        ser = CIPSimpleSerializer(cip)
        return ser.data

    def get_precise_detail(self, obj):
        try:
            cip = CIP.objects.get(area=obj.area, subarea=obj.subarea, precise=obj.precise, version=obj.version)
        except:
            return None

        if cip == obj:
            return None

        ser = CIPSimpleSerializer(cip)
        return ser.data


class ProgramOutcomeStatSerializer(serializers.ModelSerializer):
    academic_year_code = serializers.ReadOnlyField(source='academic_year.code', read_only=True)
    academic_year_display = serializers.ReadOnlyField(source='academic_year.display', read_only=True)

    class Meta:
        fields = (
            'academic_year_code',
            'academic_year_display',
            'employed_full_time',
            'continuing_education',
            'avg_annual_earnings'
        )
        model = ProgramOutcomeStat


class EmploymentProjectionSerializer(serializers.ModelSerializer):
    soc_name = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'soc_name',
            'report',
            'begin_employment',
            'end_employment',
            'change',
            'change_percentage',
            'openings',
            'report_year_begin',
            'report_year_end'
        )
        model = EmploymentProjection

    def get_soc_name(self, projection):
        return projection.soc.name


class EmploymentProjectionTotalsSerializer(serializers.Serializer):
    begin_year = serializers.IntegerField()
    end_year = serializers.IntegerField()
    begin_employment = serializers.IntegerField()
    end_employment = serializers.IntegerField()
    change = serializers.IntegerField()
    change_percentage = serializers.DecimalField(max_digits=12, decimal_places=2)
    openings = serializers.IntegerField()


class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    admission_term = serializers.StringRelatedField(many=False)
    deadline_type = serializers.StringRelatedField(many=False)

    class Meta:
        fields = (
            'admission_term',
            'deadline_type',
            'display',
            'month',
            'day',
        )
        model = ApplicationDeadline

class AcademicTermSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'full_name',
            'semester',
            'semester_index',
            'year'
        )
        model = AcademicTerm

class ProgramSerializer(DynamicFieldSetMixin, serializers.ModelSerializer):
    level = serializers.StringRelatedField(many=False)
    career = serializers.StringRelatedField(many=False)
    degree = serializers.StringRelatedField(many=False)

    descriptions = ProgramDescriptionLinkedSerializer(many=True, read_only=False)
    profiles = ProgramProfileLinkedSerializer(many=True, read_only=False)
    outcomes = serializers.HyperlinkedIdentityField(
        view_name='api.programs.outcomes',
        lookup_field='id'
    )
    projection_totals = serializers.HyperlinkedIdentityField(
        view_name='api.programs.projections',
        lookup_field='id'
    )
    careers = serializers.HyperlinkedIdentityField(
        view_name='api.programs.careers',
        lookup_field='id'
    )

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

    application_deadlines = serializers.HyperlinkedIdentityField(
        view_name='api.programs.deadlines',
        lookup_field='id'
    )
    start_term = AcademicTermSerializer(many=False, read_only=True)

    excerpt = serializers.SerializerMethodField()

    area_of_interest = serializers.SerializerMethodField()
    subarea_of_interest = serializers.SerializerMethodField()

    def get_excerpt(self, obj: Program):
        return obj.excerpt

    def get_area_of_interest(self, obj: Program):
        if obj.current_cip is None:
            return None

        try:
            top_level_cip = CIP.objects.get(code=obj.current_cip.area_code_str, version=settings.CIP_CURRENT_VERSION)
            cip_name = top_level_cip.name.title()
            return cip_name
        except CIP.DoesNotExist:
            return None

    def get_subarea_of_interest(self, obj: Program):
        if obj.current_cip is None:
            return None

        try:
            subarea_cip = CIP.objects.get(code=f"{obj.current_cip.area_code_str}.{obj.current_cip.subarea_code_str}", version=settings.CIP_CURRENT_VERSION)
            cip_name = subarea_cip.name.title()
            return cip_name
        except CIP.DoesNotExist:
            return None
            
    class Meta:
        fields = (
            'id',
            'name',
            'descriptions',
            'credit_hours',
            'online',
            'has_online',
            'profiles',
            'primary_profile_url',
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
            'tuition_type',
            'outcomes',
            'projection_totals',
            'careers',
            'application_deadlines',
            'graduate_slate_id',
            'valid',
            'has_locations',
            'active',
            'start_term',
            'excerpt',
            'area_of_interest',
            'subarea_of_interest'
        )
        fieldsets = {
            "identifiers": "id,name,plan_code,subplan_code,cip_code,parent_program",
        }
        model = Program


class CollegeOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = CollegeOverride


class TuitionOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = TuitionOverride

class WeightedJobSerializer(serializers.ModelSerializer):
    job = serializers.StringRelatedField(many=False)

    class Meta:
        fields = [
            'job',
            'weight'
        ]
        model = WeightedJobPosition
