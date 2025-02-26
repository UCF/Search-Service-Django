from rest_framework import serializers

from marketing.models import Quote

class QuoteSerializer(serializers.ModelSerializer):
    source_formatted = serializers.ReadOnlyField()

    class Meta:
        model = Quote
        fields = (
            'id',
            'quote_text',
            'source',
            'titles',
            'image',
            'source_formatted'
        )
