# -*- coding: utf-8 -*-


from django import forms as forms
from django.contrib.gis import forms as gisforms

from django.db import models
from django.contrib.gis.db import models as gismodels

from django.contrib import admin

from .models import *


# Register your models here.
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(CampusType)
class CampusTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(ParkingZone)
class ParkingZoneAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(ParkingPermitType)
class ParkingPermitTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 28.6025,
                    'default_lon': -81.20010137557983,
                    'default_zoom': 15,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    pass
    # formfield_overrides = {
    #     models.ManyToManyField: {
    #         'widget': forms.CheckboxSelectMultiple
    #     }
    # }


@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    pass
