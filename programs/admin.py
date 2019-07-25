# -*- coding: utf-8 -*-


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


@admin.register(ProgramProfileType)
class ProgramProfileTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ProgramDescriptionType)
class ProgramDescriptionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ProgramProfile)
class ProgramProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(ProgramDescription)
class ProgramDescriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    search_fields = ('name', )
    list_filter = ('level__name', 'colleges__full_name', )

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    pass

@admin.register(TuitionOverride)
class TuitionOverrideAdmin(admin.ModelAdmin):
    pass

@admin.register(CollegeOverride)
class CollegeOverrideAdmin(admin.ModelAdmin):
    pass
