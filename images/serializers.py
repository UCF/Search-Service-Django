from rest_framework import serializers

from images.models import *


class ImageSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, source='tags_with_synonyms')

    class Meta:
        fields = (
            'id',
            'filename',
            'extension',
            'source',
            'source_id',
            'source_created',
            'source_modified',
            'photo_taken',
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
