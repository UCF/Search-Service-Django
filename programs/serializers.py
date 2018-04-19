from rest_framework import serializers
from rest_framework.reverse import reverse
from programs.models import *

from django.db import IntegrityError


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
    url = serializers.HyperlinkedIdentityField(
        view_name='api.colleges.detail',
        lookup_field='id'
    )

    class Meta:
        fields = ('full_name', 'url')
        model = College


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = College


class DepartmentLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api.departments.detail',
        lookup_field='id'
    )

    class Meta:
        fields = ('full_name', 'url')
        model = Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class ProgramProfileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramProfileType


class ProgramProfileSerializer(serializers.ModelSerializer):
    profile_type = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        fields = ('profile_type', 'url', 'primary')
        model = ProgramProfile


class ProgramDescriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ProgramDescriptionType


class ProgramDescriptionSerializer(serializers.ModelSerializer):
    description_type = serializers.PrimaryKeyRelatedField(
        queryset=ProgramDescriptionType.objects.all()
    )
    program = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True,
    )

    class Meta:
        fields = ('description_type', 'description', 'primary', 'program')
        model = ProgramDescription

    def create(self, validated_data):
        try:
            program_id = self.context['view'].kwargs['program__id']
            program = Program.objects.get(id=program_id)
            validated_data.update({
                'program': program
            })
        except Program.DoesNotExist:
            raise serializers.ValidationError('Program ID provided does not exist')
        except:
            raise serializers.ValidationError('Program ID must be provided')

        try:
            description_type = validated_data.get('description_type', None)
            validated_data.update({
                'description_type': description_type
            })
        except ProgramDescriptionType.DoesNotExist:
            raise serializers.ValidationError("Description Type much exist.")

        retval = None

        try:
            retval = ProgramDescription.objects.create(**validated_data)
            retval.save()
        except IntegrityError as e:
            raise serializers.ValidationError('A description of type `{0}` already exists.'.format(description_type.name), )


        return retval

    def update(self, instance, validated_data):
        try:
            description_type = validated_data.get('description_type', None)
        except ProgramDescriptionType.DoesNotExist:
            raise serializers.ValidationError("Description Type much exist.")

        instance.description_type = description_type
        instance.description = validated_data.get('description', instance.description)
        instance.primary = validated_data.get('primary', instance.primary)

        return instance


class RelatedProgramSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api.programs.detail',
        lookup_field='id'
    )

    class Meta:
        fields = (
            'name',
            'online',
            'url'
        )
        model = Program


class ProgramSerializer(serializers.ModelSerializer):
    level = serializers.StringRelatedField(many=False)
    career = serializers.StringRelatedField(many=False)
    degree = serializers.StringRelatedField(many=False)

    descriptions = ProgramDescriptionSerializer(many=True, read_only=False)
    profiles = ProgramProfileSerializer(many=True, read_only=False)

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
            'subplans'
        )
        model = Program
