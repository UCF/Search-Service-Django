from rest_framework import serializers

from locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class LegacyLocationSerializer(serializers.ModelSerializer):
    """
    Reproduces the exact field structure of the map.ucf.edu/locations.json feed.
    Consumed by the UCF Location CPT Plugin importer and other legacy clients.
    """
    id = serializers.SerializerMethodField()
    googlemap_point = serializers.SerializerMethodField()
    illustrated_point = serializers.SerializerMethodField()
    poly_coords = serializers.SerializerMethodField()
    modified = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'profile',
            'poly_coords',
            'description',
            'image',
            'object_type',
            'modified',
            'id',
            'abbreviation',
            'illustrated_point',
            'googlemap_point',
            'profile_link',
            'name',
        ]

    def get_id(self, obj):
        return obj.location_id if obj.location_id else str(obj.pk)

    def get_googlemap_point(self, obj):
        return obj.googlemap_point

    def get_illustrated_point(self, obj):
        return obj.illustrated_point

    def get_poly_coords(self, obj):
        return obj.poly_coords_parsed

    def get_modified(self, obj):
        if obj.modified:
            return obj.modified.strftime('%Y-%m-%d %H:%M:%S')
        return None
