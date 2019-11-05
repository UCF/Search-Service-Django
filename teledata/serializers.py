from rest_framework import serializers
from rest_framework.reverse import reverse
from teledata.models import *
import warnings

from django.db import IntegrityError

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Building
