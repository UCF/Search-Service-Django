from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import ResearchWork, Researcher, ResearcherEducation

# Register your models here.
@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    pass

@admin.register(ResearcherEducation)
class ResearcherEducationAdmin(admin.ModelAdmin):
    pass

@admin.register(ResearchWork)
class ResearchWorkAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_filter = ('work_type',)
    readonly_fields = ['citation',]

    def citation(self, obj):
        return mark_safe(obj.citation)
