from rest_framework import serializers

from locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    googlemap_point = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = '__all__'

    def get_googlemap_point(self, obj):
        return obj.googlemap_point
