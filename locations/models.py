# -*- coding: utf-8 -*-
import json

from django.db import models


class Location(models.Model):
    """
    Represents a physical location on or near campus.

    Fields are sourced from two inputs:
      - The UCF Map API (map.ucf.edu/locations.json) for legacy API reproduction
      - The bulk upload Excel format for administrative imports
    """

    # Core identifier used by the legacy map API (e.g. "50", "downtown", "bikerack-1").
    # May be null for locations created via bulk upload that have no map ID.
    location_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    # MD5 hash of (name | object_type | raw location string) from the Excel importer.
    # Used as a stable unique key so duplicate-named records (e.g. multiple
    # "Shuttle Stop" entries at different coordinates) can coexist.
    # Null for records not created via the Excel importer.
    import_key = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True
    )

    # --- Fields from the legacy map API (map.ucf.edu/locations.json) ---

    name = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    # Full HTML profile content used as the primary body text
    profile = models.TextField(null=True, blank=True)
    profile_link = models.URLField(max_length=500, null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)
    image = models.CharField(max_length=500, null=True, blank=True)
    object_type = models.CharField(max_length=100, null=True, blank=True)

    # Google Maps coordinates stored as separate fields (no PostGIS on MySQL)
    googlemap_lat = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )
    googlemap_lng = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )

    # Illustrated (custom map) coordinates
    illustrated_lat = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )
    illustrated_lng = models.DecimalField(
        max_digits=17, decimal_places=14, null=True, blank=True
    )

    # Polygon boundary coordinates stored as a JSON string.
    # Format mirrors the legacy API: [[[lng, lat], [lng, lat], ...]]
    poly_coords = models.TextField(null=True, blank=True)

    modified = models.DateTimeField(null=True, blank=True)

    # --- Additional fields from the bulk upload Excel format ---

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
        return self.name or self.location_id or str(self.pk)

    @property
    def googlemap_point(self):
        if self.googlemap_lat is not None and self.googlemap_lng is not None:
            return [float(self.googlemap_lat), float(self.googlemap_lng)]
        return None

    @property
    def illustrated_point(self):
        if self.illustrated_lat is not None and self.illustrated_lng is not None:
            return [float(self.illustrated_lat), float(self.illustrated_lng)]
        return None

    @property
    def poly_coords_parsed(self):
        if self.poly_coords:
            try:
                return json.loads(self.poly_coords)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
