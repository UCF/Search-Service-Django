# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from teledata.models import Staff

from django.db import models

# Create your models here.
class Researcher(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    affiliation = models.CharField(max_length=255, null=True, blank=True)
    teledata_record = models.ForeignKey(Staff, null=True, blank=True)

class Publication(models.Model):
    title = models.CharField(max_length=1000, null=False, blank=False)
    publication_date = models.DateField()
    researcher = models.ForeignKey(Researcher)
