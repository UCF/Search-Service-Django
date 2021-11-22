from django.contrib import admin
from django.utils.safestring import mark_safe

from research.models import Article
from research.models import Book
from research.models import BookChapter
from research.models import ClinicalTrial
from research.models import ConferenceProceeding
from research.models import Grant
from research.models import HonorificAward
from research.models import Patent
from research.models import Researcher
from research.models import ResearcherEducation

# Register your models here.
@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    search_fields = ('teledata_record__first_name', 'teledata_record__last_name', 'orcid_id', 'research_terms__term_name')
    list_filter = ('employee_record__colleges__display_name',)

@admin.register(ResearcherEducation)
class ResearcherEducationAdmin(admin.ModelAdmin):
    pass

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    pass

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    pass

@admin.register(BookChapter)
class BookChapterAdmin(admin.ModelAdmin):
    pass

@admin.register(ClinicalTrial)
class ClinicalTrialAdmin(admin.ModelAdmin):
    pass

@admin.register(ConferenceProceeding)
class ConferenceProceedingAdmin(admin.ModelAdmin):
    pass


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    pass

@admin.register(HonorificAward)
class HonorificAwardAdmin(admin.ModelAdmin):
    pass

@admin.register(Patent)
class PatentAdmin(admin.ModelAdmin):
    pass
