from rest_framework import serializers
from images.models import *


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Image
