from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import ResearchWork, Researcher, ResearcherEducation

# Register your models here.
@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    search_fields = ('teledata_record__first_name', 'teledata_record__last_name', 'orcid_id')

@admin.register(ResearcherEducation)
class ResearcherEducationAdmin(admin.ModelAdmin):
    pass

@admin.register(ResearchWork)
class ResearchWorkAdmin(admin.ModelAdmin):
    pass
