from rest_framework import serializers

from .models import AutoAnchor

class AutoAnchorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoAnchor
        fields = [
            'pattern',
            'url'
        ]

class FoundPatternsSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    matches = serializers.BooleanField(read_only=True)
    patterns = AutoAnchorSerializer(many=True, read_only=True)

    class Meta:
        fields = [
            'matches',
            'patterns'
        ]
