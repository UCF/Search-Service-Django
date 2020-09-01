# -*- coding: utf-8 -*-


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
    actions = ['make_active', 'make_inactive']
    readonly_fields = ('created', 'modified', 'valid', 'has_locations', 'active_comments_author')
    search_fields = ('name', 'plan_code', 'subplan_code')
    list_filter = ('level__name', 'colleges__full_name', 'valid', 'has_locations', 'active')
    list_display = ('name', 'plan_code', 'subplan_code', 'created', 'valid', 'has_locations', 'active')

    def make_active(self, request, queryset):
        rows_updated = queryset.update(active=True)
        if rows_updated == 1:
            message_bit = '1 program was'
        else:
            message_bit = '{0} programs were'.format(rows_updated)
        self.message_user(
            request,
            '{0} successfully marked as active.'.format(message_bit)
        )
    make_active.short_description = 'Mark selected programs as active'

    def make_inactive(self, request, queryset):
        rows_updated = queryset.update(active=False)
        if rows_updated == 1:
            message_bit = '1 program was'
        else:
            message_bit = '{0} programs were'.format(rows_updated)
        self.message_user(
            request,
            '{0} successfully marked as inactive.'.format(message_bit)
        )
    make_inactive.short_description = 'Mark selected programs as inactive'

    def save_model(self, request, obj, form, change):
        if change and 'active_comments' in form.changed_data:
            new_active_comments = obj.active_comments
            if new_active_comments:
                obj.active_comments_author = request.user
            else:
                obj.active_comments_author = None

        super(ProgramAdmin, self).save_model(request, obj, form, change)



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
