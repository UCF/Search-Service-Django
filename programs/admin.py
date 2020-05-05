# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join
from django_mysql.models import ListCharField

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


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    pass


@admin.register(CIP)
class CIPAdmin(admin.ModelAdmin):
    search_fields = ('name', 'code')
    list_filter = ('version',)


@admin.register(SOC)
class SOCAdmin(admin.ModelAdmin):
    pass


@admin.register(EmploymentProjection)
class EmploymentProjectionAdmin(admin.ModelAdmin):
    pass


@admin.register(AdmissionTerm)
class AdmissionTermAdmin(admin.ModelAdmin):
    pass


@admin.register(AdmissionDeadlineType)
class AdmissionDeadlineTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ApplicationDeadline)
class ApplicationDeadlineAdmin(admin.ModelAdmin):
    readonly_fields = ['programs_list']
    list_filter = ('admission_term', 'career', 'deadline_type', 'month',)

    def programs_list(self, obj):
        programs = Program.objects.filter(application_deadlines=obj)
        if programs.count() == 0:
            return '(None)'

        program_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:programs_program_change',
                        args=(program.pk,)
                    ),
                    program.name
                )
                for program in programs
            )
        )

        return '{0} Programs:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            programs.count(),
            program_list_items
        )

    programs_list.allow_tags = True
    programs_list.short_description = 'Program(s)'
