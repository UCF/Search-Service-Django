# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-01-10 19:51


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0003_auto_20200110_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='source_created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='image',
            name='source_modified',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
