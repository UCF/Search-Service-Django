from django.db import models

# Create your models here.
class InternalLinkManager(models.Manager):
    def find_in_text(self, text: str):
        link_ids = []

        for link in self.all():
            if any([phrase.phrase.lower() in text.lower() for phrase in link.phrases.all()]):
                link_ids.append(link.id)

        return self.filter(id__in=link_ids)

class InternalLink(models.Model):
    url = models.URLField(max_length=255, null=False, blank=False)
    imported = models.BooleanField(default=False)
    objects = InternalLinkManager()

    def __str__(self):
        return self.url

class KeywordPhrase(models.Model):
    phrase = models.CharField(max_length=255, null=False, blank=False)
    link = models.ForeignKey(InternalLink, related_name='phrases', on_delete=models.CASCADE)

    def __str__(self):
        return self.phrase
