# -*- coding: utf-8 -*-

from django.conf import settings
from django.urls import reverse
from django.utils.html import mark_safe
from django.contrib import admin

from django import forms as forms
from django.contrib.gis import forms as gisforms
from django.contrib.gis.db import models as gismodels

from .models import *


# Register your models here.
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'site_id', 'campus_type', 'has_point')
    ordering = ['name']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }

    @admin.display(boolean=True)
    def has_point(self, obj):
        return True if obj.point_coords else False


@admin.register(CampusType)
class CampusTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    ordering = ['name']

    def count(self, obj):
        return mark_safe(
            '<a href="{0}?campus_type={1}">{2}</a>'.format(
                reverse(
                    'admin:locations_campus_changelist'
                ),
                obj.pk,
                Campus.objects.filter(campus_type=obj).count()
            )
        )


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'building_id', 'abbreviation', 'has_point', 'has_polygon')
    ordering = ['name']
    search_fields = ['name', 'building_id', 'abbreviation']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }

    @admin.display(boolean=True)
    def has_point(self, obj):
        return True if obj.point_coords else False

    @admin.display(boolean=True)
    def has_polygon(self, obj):
        return True if obj.poly_coords else False


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'building_id', 'abbreviation', 'has_point', 'has_polygon')
    ordering = ['name']
    search_fields = ['name', 'building_id', 'abbreviation']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }

    @admin.display(boolean=True)
    def has_point(self, obj):
        return True if obj.point_coords else False

    @admin.display(boolean=True)
    def has_polygon(self, obj):
        return True if obj.poly_coords else False


@admin.register(ParkingZone)
class ParkingZoneAdmin(admin.ModelAdmin):
    ordering = ['name']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }


@admin.register(ParkingPermitType)
class ParkingPermitTypeAdmin(admin.ModelAdmin):
    ordering = ['name']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'import_id', 'location_type', 'has_point', 'has_polygon')
    ordering = ['name']
    search_fields = ['name']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }

    @admin.display(boolean=True)
    def has_point(self, obj):
        return True if obj.point_coords else False

    @admin.display(boolean=True)
    def has_polygon(self, obj):
        return True if obj.poly_coords else False


@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    ordering = ['name']

    def count(self, obj):
        return mark_safe(
            '<a href="{0}?location_type={1}">{2}</a>'.format(
                reverse(
                    'admin:locations_location_changelist'
                ),
                obj.pk,
                Location.objects.filter(location_type=obj).count()
            )
        )


@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'point_type', 'has_point', 'has_polygon')
    ordering = ['name']
    search_fields = ['name']

    formfield_overrides = {
        gismodels.PointField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
        gismodels.PolygonField: {
            'widget': gisforms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': settings.LOCATIONS_OSMWIDGET_DEFAULT_LAT,
                    'default_lon': settings.LOCATIONS_OSMWIDGET_DEFAULT_LON,
                    'default_zoom': settings.LOCATIONS_OSMWIDGET_DEFAULT_ZOOM,
                    'display_raw': True
                }
            )
        },
    }

    @admin.display(boolean=True)
    def has_point(self, obj):
        return True if obj.point_coords else False

    @admin.display(boolean=True)
    def has_polygon(self, obj):
        return True if obj.poly_coords else False


@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    ordering = ['name']

    def count(self, obj):
        return mark_safe(
            '<a href="{0}?point_type={1}">{2}</a>'.format(
                reverse(
                    'admin:locations_pointofinterest_changelist'
                ),
                obj.pk,
                PointOfInterest.objects.filter(point_type=obj).count()
            )
        )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    ordering = ['name']
    autocomplete_fields = ['facilities', 'parking_lots', 'locations', 'points_of_interest']


@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    ordering = ['name']

    def count(self, obj):
        return mark_safe(
            '<a href="{0}?group_type={1}">{2}</a>'.format(
                reverse(
                    'admin:locations_group_changelist'
                ),
                obj.pk,
                Group.objects.filter(group_type=obj).count()
            )
        )
