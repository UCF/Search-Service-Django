# -*- coding: utf-8 -*-


from django.db import models

# Create your models here.


class LowercaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(LowercaseCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super(LowercaseCharField, self).get_prep_value(value)
        if value is not None:
            return value.lower()
        return ''
