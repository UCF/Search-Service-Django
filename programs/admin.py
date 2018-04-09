# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import *

# Register your models here.
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    pass

@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    pass

@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    pass

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    pass

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    pass

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    pass
