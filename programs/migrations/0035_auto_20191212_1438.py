# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-12 14:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0034_employmentprojection'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='soc',
            name='cip',
        ),
        migrations.AddField(
            model_name='soc',
            name='cip',
            field=models.ManyToManyField(related_name='occupations', to='programs.CIP'),
        ),
    ]
