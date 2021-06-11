from django.contrib import admin

from org_units.models import *

# Register your models here.


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    pass


@admin.register(DepartmentUnit)
class DepartmentUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    pass
