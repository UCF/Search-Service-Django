from django.contrib import admin

from .models import Researcher

# Register your models here.
@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    pass
