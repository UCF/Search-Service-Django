# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-11-06 15:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teledata', '0005_auto_20191104_1429'),
    ]

    operations = [
        migrations.RenameField(
            model_name='building',
            old_name='abrev',
            new_name='abbr',
        ),
        migrations.RenameField(
            model_name='building',
            old_name='descr',
            new_name='description',
        ),
    ]