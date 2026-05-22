from django.contrib import admin

from locations.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'location_id', 'object_type', 'abbreviation',
        'visible', 'private', 'is_verified', 'modified',
    ]
    list_filter = ['object_type', 'visible', 'private', 'is_verified']
    search_fields = ['name', 'location_id', 'abbreviation', 'description', 'keywords']
    readonly_fields = ['modified']
