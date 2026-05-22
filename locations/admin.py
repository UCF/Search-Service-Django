from django.contrib import admin

from locations.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'object_type', 'abbreviation',
        'visible', 'private', 'is_verified',
    ]
    list_filter = ['object_type', 'visible', 'private', 'is_verified']
    search_fields = ['name', 'abbreviation', 'description', 'keywords']
