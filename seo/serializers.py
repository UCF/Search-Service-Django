from rest_framework import serializers

from .models import InternalLink

class InternalLinkSerializer(serializers.ModelSerializer):
    phrases = serializers.StringRelatedField(many=True)

    class Meta:
        model = InternalLink
        fields = [
            'url',
            'phrases'
        ]
