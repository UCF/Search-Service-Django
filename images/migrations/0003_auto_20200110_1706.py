# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-01-10 17:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0002_auto_20200109_1355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagetag',
            name='synonyms',
            field=models.ManyToManyField(blank=True, to='images.ImageTag'),
        ),
    ]