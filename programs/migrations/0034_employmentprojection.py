# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-11 19:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0033_jobposition_soc'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmploymentProjection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report', models.CharField(choices=[('1828', '2018-2028')], default=b'1828', max_length=4)),
                ('begin_employment', models.IntegerField()),
                ('end_employment', models.IntegerField()),
                ('change', models.IntegerField()),
                ('change_percentage', models.DecimalField(decimal_places=2, max_digits=12)),
                ('openings', models.IntegerField()),
                ('soc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projections', to='programs.SOC')),
            ],
        ),
    ]