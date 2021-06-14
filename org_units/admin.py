from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe

from org_units.models import *

# Register your models here.


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('dept_unit_list', 'teledata_list', 'college',)

    def teledata_list(self, obj):
        teledata_orgs = obj.teledata.all()
        if teledata_orgs.count() == 0:
            return '-'

        org_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:teledata_organization_change',
                        args=(teledata_org.pk,)
                    ),
                    teledata_org.name
                )
                for teledata_org in teledata_orgs
            )
        )

        return mark_safe('{0} Teledata Organizations:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            teledata_orgs.count(),
            org_list_items
        ))

    teledata_list.allow_tags = True
    teledata_list.short_description = 'Teledata Organization(s)'

    def dept_unit_list(self, obj):
        dept_units = obj.department_units.all()
        if dept_units.count() == 0:
            return '-'

        dept_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:org_units_departmentunit_change',
                        args=(dept_unit.pk,)
                    ),
                    dept_unit.name
                )
                for dept_unit in dept_units
            )
        )

        return mark_safe('{0} Department Units:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            dept_units.count(),
            dept_list_items
        ))

    dept_unit_list.allow_tags = True
    dept_unit_list.short_description = 'Department Unit(s)'


@admin.register(DepartmentUnit)
class DepartmentUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('teledata_list', 'program_dept_list',)

    def teledata_list(self, obj):
        teledata_depts = obj.teledata.all()
        if teledata_depts.count() == 0:
            return '-'

        dept_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:teledata_department_change',
                        args=(teledata_dept.pk,)
                    ),
                    teledata_dept.name
                )
                for teledata_dept in teledata_depts
            )
        )

        return mark_safe('{0} Teledata Departments:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            teledata_depts.count(),
            dept_list_items
        ))

    teledata_list.allow_tags = True
    teledata_list.short_description = 'Teledata Department(s)'

    def program_dept_list(self, obj):
        program_depts = obj.program_data.all()
        if program_depts.count() == 0:
            return '-'

        dept_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:programs_department_change',
                        args=(program_dept.pk,)
                    ),
                    program_dept.full_name
                )
                for program_dept in program_depts
            )
        )

        return mark_safe('{0} Program Departments:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            program_depts.count(),
            dept_list_items
        ))

    program_dept_list.allow_tags = True
    program_dept_list.short_description = 'Program Department(s)'
