# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-06 14:59


from django.db import migrations, models
import django.db.models.deletion

from programs.models import ProgramOutcomeStat

class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0030_auto_20191205_1727'),
    ]

    operations = [
        migrations.RunSQL(
            'TRUNCATE TABLE `programs_programoutcomestat`',
            'TRUNCATE TABLE `programs_programoutcomestat`'
        ),
        migrations.RemoveField(
            model_name='programoutcomestat',
            name='program',
        ),
        migrations.AddField(
            model_name='program',
            name='outcomes',
            field=models.ManyToManyField(related_name='programs', to='programs.ProgramOutcomeStat'),
        ),
        migrations.AddField(
            model_name='programoutcomestat',
            name='cip',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='programs.CIP'),
            preserve_default=False,
        ),
    ]
