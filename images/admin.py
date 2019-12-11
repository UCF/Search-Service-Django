# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import *

# Register your models here.


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    search_fields = ('filename',)


@admin.register(ImageTag)
class ImageTagAdmin(admin.ModelAdmin):
    pass
