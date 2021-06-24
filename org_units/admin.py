from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe

from org_units.models import *

# Register your models here.


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('parent_unit', 'child_units_list', 'college', 'teledata_orgs_list', 'teledata_depts_list', 'program_depts_list' )

    def child_units_list(self, obj):
        child_units = obj.child_units.all()
        if child_units.count() == 0:
            return '-'

        child_list_items = format_html_join(
            '\n',
            '<li><a href="{0}">{1}</a></li>',
            (
                (
                    reverse(
                        'admin:org_units_unit_change',
                        args=(child_unit.pk,)
                    ),
                    child_unit.name
                )
                for child_unit in child_units
            )
        )

        return mark_safe('{0} Child Units:\n<ul style="margin-left: 0; margin-top: 1rem; padding-left: 0;">{1}</ul>'.format(
            child_units.count(),
            child_list_items
        ))

    child_units_list.allow_tags = True
    child_units_list.short_description = 'Child Unit(s)'

    def teledata_orgs_list(self, obj):
        teledata_orgs = obj.teledata_organizations.all()
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

    teledata_orgs_list.allow_tags = True
    teledata_orgs_list.short_description = 'Teledata Organization(s)'

    def teledata_depts_list(self, obj):
        teledata_depts = obj.teledata_departments.all()
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

    teledata_depts_list.allow_tags = True
    teledata_depts_list.short_description = 'Teledata Department(s)'

    def program_depts_list(self, obj):
        program_depts = obj.program_departments.all()
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

    program_depts_list.allow_tags = True
    program_depts_list.short_description = 'Program Department(s)'
