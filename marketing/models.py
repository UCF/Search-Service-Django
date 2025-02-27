from django.db import models

from taggit.managers import TaggableManager

import re

from programs.models import Program

# Create your models here.
class Quote(models.Model):
    quote_text = models.TextField(null=False, blank=False)
    source = models.CharField(null=True, blank=True, max_length=500)
    titles = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    tags = TaggableManager('tags')
    programs = models.ManyToManyField(Program, blank=True, related_name='quotes')

    def __str__(self):
        if self.source:
            return f"{self.source}: {self.quote_text}"
        else:
            return self.quote_text

    @property
    def source_formatted(self):
        pattern = r'(.*[\’\']\d{2}([a-zA-Z.]+)?)'
        return re.sub(pattern, '<strong>\g<1></strong>', f"{self.source} {self.titles}")
