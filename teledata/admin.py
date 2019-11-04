# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import *

# Register your models here.
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    pass

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    pass

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    pass
