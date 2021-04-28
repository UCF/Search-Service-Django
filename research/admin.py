from django.contrib import admin

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
    pass
