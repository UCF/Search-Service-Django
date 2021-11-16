from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe

from units.models import *

# Register your models here.


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('name', 'parent_unit_link', 'child_units_list', 'college_link', 'teledata_orgs_list', 'teledata_depts_list', 'program_depts_list',)
    exclude = ('parent_unit', 'college',)

    def parent_unit_link(self, obj):
        return mark_safe(
            '<a href="{0}">{1}</a>'.format(
                reverse(
                    'admin:units_unit_change',
                    args=(obj.parent_unit.pk,)
                ),
                obj.parent_unit.name
            )
        )

    parent_unit_link.allow_tags = True
    parent_unit_link.short_description = 'Parent Unit'

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
                        'admin:units_unit_change',
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

    def college_link(self, obj):
        return mark_safe(
            '<a href="{0}">{1}</a>'.format(
                reverse(
                    'admin:programs_college_change',
                    args=(obj.college.pk,)
                ),
                obj.college.full_name
            )
        )

    college_link.allow_tags = True
    college_link.short_description = 'College'

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


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    pass

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ('ext_org_id', 'ext_org_name', 'sanitized_name', 'display_name')
    include_fields = '__all__'

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    search_fields = ('ext_college_name', 'sanitized_name', 'display_name',)
    readonly_fields = ('ext_college_name', 'programs_college_link',)
    include_fields = [
        'ext_college_name',
        'sanitized_name',
        'display_name',
        'programs_college_link'
    ]

    def programs_college_link(self, obj):
        if obj.program_college.count() == 0:
            return mark_safe('<p style="margin-top: 0;">0 Program Colleges</p>')

        retval = '<ul style="margin-left: 0; margin-top: 0; padding-left: 0;">'

        for college in obj.program_college.all():
            retval += '<li><a href="{0}">{1}</a></li>'.format(
                reverse(
                    'admin:programs_college_change',
                    args=(college.pk,)
                ),
                college.full_name
            )

        retval += '</ul>'

        return mark_safe(retval)

    programs_college_link.allow_tags = True
    programs_college_link.short_description = 'Program College'


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    search_fields = ('ext_division_name', 'sanitized_name', 'display_name')
    include_fields = '__all__'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('ext_department_id', 'ext_department_name', 'sanitized_name', 'display_name',)
    readonly_fields = ('ext_department_id', 'ext_department_name', 'programs_department_link',)
    include_fields = '__all__'

    def programs_department_link(self, obj):
        if obj.program_department.count() == 0:
            return mark_safe('<p style="margin-top: 0;">0 Program Departments</p>')

        retval = '<ul style="margin-left: 0; margin-top: 0; padding-left: 0;">'

        for dept in obj.program_department.all():
            retval += '<li><a href="{0}">{1}</a></li>'.format(
                reverse(
                    'admin:programs_department_change',
                    args=(dept.pk,)
                ),
                dept.full_name
            )

        retval += '</ul>'

        return mark_safe(retval)

    programs_department_link.allow_tags = True
    programs_department_link.short_description = 'Program Department'
