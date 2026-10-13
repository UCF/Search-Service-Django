# -*- coding: utf-8 -*-


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from core.models import ExtendedUser
from programs.models import College, Department

# Register your models here.
class ExtendedUserInline(admin.StackedInline):
    model = ExtendedUser
    can_delete = False
    verbose_name_plural = 'Program Permissions'

class UserAdmin(BaseUserAdmin):
    inlines = [
        ExtendedUserInline
    ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


def has_admin_access(user):
    """
    Whether the user can use the admin. Django's default requires staff
    status; superusers are let in without it. The SAML signin view uses
    this too, so the two never disagree and send a user in a loop.
    """
    return user.is_active and (user.is_staff or user.is_superuser)


admin.site.has_permission = lambda request: has_admin_access(request.user)
