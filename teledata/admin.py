# -*- coding: utf-8 -*-


from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import mark_safe

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
    exclude = ('unit',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            readonly = [item.name for item in obj._meta.fields]
            readonly.remove('active')
            readonly.remove('unit')
            readonly.append('unit_link')
            return self.readonly_fields + tuple(readonly)
        return self.readonly_fields

    def unit_link(self, obj):
        return mark_safe(
            '<a href="{0}">{1}</a>'.format(
                reverse(
                    'admin:units_unit_change',
                    args=(obj.unit.pk,)
                ),
                obj.unit.name
            )
        )

    unit_link.allow_tags = True
    unit_link.short_description = 'Unit'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    inlines = [
        KeywordInline
    ]
    search_fields = ('name',)
    exclude = ('unit',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            readonly = [item.name for item in obj._meta.fields]
            readonly.remove('active')
            readonly.remove('unit')
            readonly.append('unit_link')
            return self.readonly_fields + tuple(readonly)
        return self.readonly_fields

    def unit_link(self, obj):
        return mark_safe(
            '<a href="{0}">{1}</a>'.format(
                reverse(
                    'admin:units_unit_change',
                    args=(obj.unit.pk,)
                ),
                obj.unit.name
            )
        )

    unit_link.allow_tags = True
    unit_link.short_description = 'Unit'


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    inlines = [
        KeywordInline
    ]
    search_fields = ('first_name', 'last_name',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            readonly = [item.name for item in obj._meta.fields]
            readonly.remove('active')
            return self.readonly_fields + tuple(readonly)
        return self.readonly_fields


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    search_fields = ('phrase',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'content_type':
            kwargs['queryset'] = ContentType.objects.filter(
                app_label='teledata',
                model__in=['staff', 'organization', 'department']
            )
        return super(KeywordAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
