from django.db import models

import re

# Create your models here.
class Quote(models.Model):
    quote_text = models.TextField(null=False, blank=False)
    speaker = models.CharField(null=True, blank=True, max_length=500)
    titles = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return f"{self.speaker}: {self.quote_text}"

    @property
    def titles_formatted(self):
        pattern = r'(.*[\’\']\d{2}([a-zA-Z.]+)?)'
        return re.sub(pattern, '<strong>\g<1></strong>', self.title)
