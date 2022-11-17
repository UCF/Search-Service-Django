from django.contrib import admin

from .models import InternalLink, KeywordPhrase

# Register your models here.

class KeywordPhraseInline(admin.TabularInline):
    model = KeywordPhrase

@admin.register(InternalLink)
class InternalLinkAdmin(admin.ModelAdmin):
    list_display = ['url', 'keywords',  'imported', 'local']
    search_fields = ['pattern', 'url']
    inlines = [
        KeywordPhraseInline
    ]
