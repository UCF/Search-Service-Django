from django.contrib import admin

from .models import AutoAnchor

# Register your models here.
@admin.register(AutoAnchor)
class AutoAnchorAdmin(admin.ModelAdmin):
    pass
