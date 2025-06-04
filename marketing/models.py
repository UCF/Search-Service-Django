from django.db import models
from django.contrib.auth.models import User

from taggit.managers import TaggableManager

import re

# Create your models here.
class Quote(models.Model):
    quote_text = models.TextField(null=False, blank=False)
    source = models.CharField(null=True, blank=True, max_length=500)
    titles = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    tags = TaggableManager()
    image_alt = models.CharField(null=True, blank=True, max_length=500)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quotes')

    def __str__(self):
        if self.source:
            return f"{self.source}"
        else:
            return self.quote_text

    @property
    def source_formatted(self):
        full_text = f"{self.source or ''} {self.titles or ''}".strip()

        match = re.match(r"(.*[’']\d{2}(?:[a-zA-Z]+)?)(.*)", full_text)
        if match:
            bold_part = match.group(1).strip()
            rest_part = match.group(2)
            return f"<strong>{bold_part}</strong>{rest_part}"
        return full_text
