# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-04 15:42


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0027_auto_20191204_1526'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cip',
            name='prev_version',
        ),
        migrations.AlterField(
            model_name='cip',
            name='next_version',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='previous_version', to='programs.CIP'),
        ),
    ]
