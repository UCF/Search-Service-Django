from rest_framework import serializers

from images.models import *


class ImageSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, source='tags_with_synonyms')

    class Meta:
        fields = (
            'created',
            'modified',
            'filename',
            'extension',
            'source',
            'copyright',
            'contributor',
            'width_full',
            'height_full',
            'download_url',
            'thumbnail_url',
            'caption',
            'tags'
        )
        model = Image
