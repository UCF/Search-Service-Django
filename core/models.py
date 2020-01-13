# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class LowercaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(LowercaseCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super(LowercaseCharField, self).get_prep_value(value)
        return value.lower()
