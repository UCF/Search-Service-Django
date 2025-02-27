from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from marketing.models import Quote

class QuoteSerializer(TaggitSerializer, serializers.ModelSerializer):
    source_formatted = serializers.ReadOnlyField()
    tags = TagListSerializerField()

    class Meta:
        model = Quote
        fields = (
            'id',
            'quote_text',
            'source',
            'titles',
            'image',
            'source_formatted',
            'tags'
        )
