# -*- coding: utf-8 -*-
from django.db import models


def _location_image_storage():
    """
    Returns LocationImageStorage (S3) when USE_S3 is enabled,
    otherwise returns a local FileSystemStorage under MEDIA_ROOT/locations/.
    """
    import os
    from django.conf import settings
    if getattr(settings, 'USE_S3', False):
        from locations.storage_backends import LocationImageStorage
        return LocationImageStorage()
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'locations'))


class Location(models.Model):
    """
    Represents a physical location on or near campus.
    Fields are sourced from the bulk upload Excel format.
    """

    # MD5 hash of the raw location (lat,lng) string from the Excel importer.
    # Used as a stable unique key so duplicate-named records can coexist.
    import_key = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(
        upload_to='',
        storage=_location_image_storage,
        null=True,
        blank=True
    )
    object_type = models.CharField(max_length=100, null=True, blank=True)

    # Google Maps coordinates stored as separate fields (no PostGIS on MySQL)
    googlemap_lat = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )
    googlemap_lng = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )

    keywords = models.TextField(null=True, blank=True)
    labels = models.CharField(max_length=500, null=True, blank=True)
    video = models.URLField(max_length=500, null=True, blank=True)
    feed_url = models.URLField(max_length=500, null=True, blank=True)
    rate = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=100, null=True, blank=True)
    data_source = models.CharField(max_length=255, null=True, blank=True)
    visible = models.BooleanField(default=True)
    private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name or str(self.pk)

    @property
    def googlemap_point(self):
        if self.googlemap_lat is not None and self.googlemap_lng is not None:
            return [float(self.googlemap_lat), float(self.googlemap_lng)]
        return None
