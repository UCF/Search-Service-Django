# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


# TODO add object overrides to enforce case-insensitivity on tag names
class ImageTag(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    synonyms = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True
    )
    source = models.CharField(max_length=255, null=True, blank=True, default='UCF Search Service')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.source:
            self.source = 'UCF Search Service'

        super(ImageTag, self).save(*args, **kwargs)


class Image(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=False)
    modified = models.DateTimeField(auto_now=True, null=False)
    filename = models.CharField(max_length=500, null=False, blank=False)
    extension = models.CharField(max_length=255, null=False, blank=False)
    source = models.CharField(max_length=255, null=True, blank=True, default='UCF Search Service')
    source_id = models.CharField(max_length=255, null=True, blank=True)
    copyright = models.CharField(max_length=255, null=True, blank=True)
    contributor = models.CharField(max_length=500, null=True, blank=True)
    width_full = models.IntegerField(null=False, blank=False)
    height_full = models.IntegerField(null=False, blank=False)
    download_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    caption = models.CharField(max_length=500, null=True, blank=True)
    tags = models.ManyToManyField(ImageTag, blank=True, related_name='images')

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.source:
            self.source = 'UCF Search Service'
            self.source_id = self.pk
        if not self.source_id:
            self.source_id = self.pk

        super(Image, self).save(*args, **kwargs)
