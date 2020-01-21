from rest_framework import serializers

from images.models import *


class ImageSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(
        many=True,
        source='tags_with_synonyms'
    )

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
            'location',
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


class ImageSearchSerializer(serializers.ModelSerializer):
    score = serializers.DecimalField(
        max_digits=20,
        decimal_places=10
    )
    tags = serializers.StringRelatedField(
        many=True,
        source='tags_with_synonyms'
    )

    class Meta:
        fields = (
            'score',
            'id',
            'filename',
            'extension',
            'source',
            'source_id',
            'source_created',
            'source_modified',
            'photo_taken',
            'location',
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
