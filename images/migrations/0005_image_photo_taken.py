# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-01-13 15:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0004_auto_20200110_1951'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='photo_taken',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]