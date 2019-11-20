# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import *

# Inline here
class KeywordInline(GenericTabularInline):
    model = Keyword

# Register your models here.
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    pass

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [
        KeywordInline
    ]
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    inlines = [
        KeywordInline
    ]
    search_fields = ('name',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    inlines = [
        KeywordInline
    ]
    search_fields = ('first_name','last_name',)

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    search_fields = ('phrase',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'content_type':
            kwargs['queryset'] = ContentType.objects.filter(app_label='teledata', model__in=['staff', 'organization', 'department'])
        return super(KeywordAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
