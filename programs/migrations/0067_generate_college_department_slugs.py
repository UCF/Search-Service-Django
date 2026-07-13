# -*- coding: utf-8 -*-
"""
Data migration that backfills WordPress-style slugs for all existing
College and Department records that don't have one yet.
"""

from django.db import migrations, models

from core.utils.slugs import wordpress_slugify


def _college_name(college):
    """
    Replicates programs.College.name for the historical model
    (historical models don't carry model properties).
    """
    unit_college = college.unit_college
    if unit_college:
        return (
            unit_college.display_name
            or unit_college.sanitized_name
            or unit_college.ext_college_name
        )
    return college.full_name


def _department_name(department):
    """
    Replicates programs.Department.name for the historical model.
    """
    unit_department = department.unit_department
    if unit_department:
        return (
            unit_department.display_name
            or unit_department.sanitized_name
            or unit_department.ext_department_name
        )
    return department.full_name


def _next_unique_slug(base, used):
    """
    Returns ``base`` (or ``base-2``, ``base-3``, ...) so it doesn't collide
    with any slug already in ``used``, matching wp_unique_post_slug().
    """
    if not base:
        return base

    slug = base
    suffix = 2
    while slug in used:
        slug = '{0}-{1}'.format(base, suffix)
        suffix += 1

    used.add(slug)
    return slug


def _backfill(model, name_getter):
    empty = models.Q(slug__isnull=True) | models.Q(slug='')

    used = set(
        model.objects.exclude(empty).values_list('slug', flat=True)
    )

    for obj in model.objects.filter(empty):
        slug = _next_unique_slug(wordpress_slugify(name_getter(obj)), used)
        if slug:
            obj.slug = slug
            obj.save(update_fields=['slug'])


def generate_slugs(apps, schema_editor):
    College = apps.get_model('programs', 'College')
    Department = apps.get_model('programs', 'Department')

    _backfill(College, _college_name)
    _backfill(Department, _department_name)


def clear_slugs(apps, schema_editor):
    College = apps.get_model('programs', 'College')
    Department = apps.get_model('programs', 'Department')

    College.objects.update(slug=None)
    Department.objects.update(slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0066_college_slug_department_slug'),
    ]

    operations = [
        migrations.RunPython(generate_slugs, clear_slugs),
    ]
