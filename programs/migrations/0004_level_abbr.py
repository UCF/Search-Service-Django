# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-09 20:44


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0003_auto_20180409_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='level',
            name='abbr',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
