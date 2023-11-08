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