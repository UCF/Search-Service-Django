# -*- coding: utf-8 -*-
"""
Slug helpers that mirror the way WordPress generates post slugs so that
slugs stay consistent between this service and WordPress-based sites.

WordPress builds a post slug by running the title through
``sanitize_title()`` (which calls ``remove_accents()``) and then
``sanitize_title_with_dashes()``, and finally ensures uniqueness via
``wp_unique_post_slug()`` by appending a numeric suffix on collision.
``wordpress_slugify()`` and ``unique_slug()`` below replicate that
behavior for the common (ASCII/English) cases we deal with.
"""

import re
import unicodedata


def wordpress_slugify(value):
    """
    Generate a slug from ``value`` using logic that mirrors WordPress's
    ``sanitize_title()`` / ``sanitize_title_with_dashes()`` as closely as
    practical.
    """
    if not value:
        return ''

    # Strip any HTML tags.
    value = re.sub(r'<[^>]*>', '', value)
    # Transliterate accented characters to ASCII (WP: remove_accents()).
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    # Lowercase.
    value = value.lower()
    # Convert forward slashes to hyphens (WP 'save' context).
    value = value.replace('/', '-')
    # Strip HTML entities (e.g. "&amp;", "&#8211;").
    value = re.sub(r'&.+?;', '', value)
    # Convert periods to hyphens.
    value = value.replace('.', '-')
    # Remove anything that isn't alphanumeric, whitespace, underscore or hyphen.
    value = re.sub(r'[^a-z0-9 _-]', '', value)
    # Collapse whitespace runs into single hyphens.
    value = re.sub(r'\s+', '-', value)
    # Collapse repeated hyphens.
    value = re.sub(r'-+', '-', value)
    # Trim leading/trailing hyphens.
    return value.strip('-')


def unique_slug(model_cls, value, slug_field='slug', pk=None):
    """
    Return a WordPress-style slug for ``value`` that is unique across
    ``model_cls``. On collision a numeric suffix is appended (``-2``,
    ``-3``, ...), matching WordPress's ``wp_unique_post_slug()``.

    ``pk`` (when provided) is excluded from the uniqueness check so an
    object doesn't collide with its own existing slug.
    """
    base = wordpress_slugify(value)
    if not base:
        return base

    max_length = getattr(model_cls._meta.get_field(slug_field), 'max_length', None)
    if max_length:
        base = base[:max_length].strip('-')

    queryset = model_cls._default_manager.all()
    if pk is not None:
        queryset = queryset.exclude(pk=pk)

    slug = base
    suffix = 2
    while queryset.filter(**{slug_field: slug}).exists():
        suffix_str = f"-{suffix}"
        if max_length:
            trimmed = base[: max_length - len(suffix_str)].rstrip('-')
            slug = f"{trimmed}{suffix_str}"
        else:
            slug = f"{base}{suffix_str}"
        suffix += 1

    return slug
