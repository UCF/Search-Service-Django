# Generated by Django 3.2.8 on 2021-11-15 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('units', '0005_auto_20211115_1516'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobTitle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ext_job_id', models.CharField(max_length=10)),
                ('ext_job_name', models.CharField(max_length=255)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='job_titles',
            field=models.ManyToManyField(related_name='employees', to='units.JobTitle'),
        ),
    ]