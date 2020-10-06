# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import models
from django.db.models import When, Case, Q
from django_mysql.models import QuerySetMixin

import core.models

# Create your models here.


class ImageTag(models.Model):
    name = core.models.LowercaseCharField(max_length=255, unique=True, null=False, blank=False)
    synonyms = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False
    )
    source = models.CharField(max_length=255, null=True, blank=True, default=settings.APP_NAME)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.source:
            self.source = settings.APP_NAME

        super(ImageTag, self).save(*args, **kwargs)


class ImageManager(models.Manager, QuerySetMixin):
    """
    Custom manager that allows for special query scoring
    """

    def search(self, search_query):
        tag_score = Case(
            When(
                (
                    Q(tags__name=search_query)
                    | Q(tags__synonyms__name=search_query)
                ),
                then=40
            ),
            default=0,
            output_field=models.DecimalField()
        )

        caption_score = Case(
            When(
                caption=search_query,
                then=15
            ),
            default=0,
            output_field=models.DecimalField()
        )

        location_score = Case(
            When(
                location=search_query,
                then=20
            ),
            default=0,
            output_field=models.DecimalField()
        )

        tag_partial_score = Case(
            When(
                (
                    Q(tags__name__icontains=search_query)
                    | Q(tags__synonyms__name__icontains=search_query)
                ),
                then=10
            ),
            default=0,
            output_field=models.DecimalField()
        )

        caption_partial_score = Case(
            When(
                caption__icontains=search_query,
                then=5
            ),
            default=0,
            output_field=models.DecimalField()
        )

        location_partial_score = Case(
            When(
                location__icontains=search_query,
                then=10
            ),
            default=0,
            output_field=models.DecimalField()
        )

        queryset = self.annotate(
            score=(
                tag_score +
                caption_score +
                location_score +
                tag_partial_score +
                caption_partial_score +
                location_partial_score
            )
        ).filter(
            score__gt=0
        ).distinct()

        return queryset


class Image(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=False)
    modified = models.DateTimeField(auto_now=True, null=False)
    last_imported = models.DateTimeField(null=True, blank=True)
    filename = models.CharField(max_length=500, null=False, blank=False)
    extension = models.CharField(max_length=255, null=False, blank=False)
    source = models.CharField(max_length=255, null=True, blank=True, default=settings.APP_NAME)
    source_id = models.CharField(max_length=255, null=True, blank=True)
    source_created = models.DateTimeField(auto_now=False, null=True, blank=True)
    source_modified = models.DateTimeField(auto_now=False, null=True, blank=True)
    photo_taken = models.DateTimeField(auto_now=False, null=True, blank=True)
    location = models.CharField(max_length=500, null=True, blank=True)
    copyright = models.CharField(max_length=255, null=True, blank=True)
    contributor = models.CharField(max_length=500, null=True, blank=True)
    width_full = models.IntegerField(null=False, blank=False)
    height_full = models.IntegerField(null=False, blank=False)
    download_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    caption = models.CharField(max_length=500, null=True, blank=True)
    tags = models.ManyToManyField(ImageTag, blank=True, related_name='images')
    objects = ImageManager()

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.source:
            self.source = settings.APP_NAME
            self.source_id = self.pk
            self.source_created = self.created
        if self.source == settings.APP_NAME:
            self.source_modified = self.modified

        super(Image, self).save(*args, **kwargs)

    @property
    def tags_with_synonyms(self):
        tags = self.tags.all()
        synonyms = ImageTag.objects.filter(synonyms__in=tags)
        return tags.union(synonyms)
