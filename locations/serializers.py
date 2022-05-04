from rest_framework import serializers
from locations.models import *


class CampusTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name']
        model = CampusType


class CampusSerializer(serializers.ModelSerializer):
    campus_type = CampusTypeSerializer()

    class Meta:
        fields = '__all__'
        model = Campus


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Facility


class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ParkingLot


class ParkingPermitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ParkingPermitType


class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ParkingZone


class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = LocationType


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Location


class PointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PointType


class PointOfInterestSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = PointOfInterest


class GroupTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = GroupType


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Group
