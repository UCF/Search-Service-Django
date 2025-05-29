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
        return f"{self.source} {self.titles}"
