# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-04 15:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0024_auto_20191203_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='cip',
            name='description',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cip',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]