# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-09 17:44


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramProfile',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('url', models.URLField()),
                ('primary', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramProfileType',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('root_url', models.URLField()),
            ],
        ),
        migrations.AlterField(
            model_name='program',
            name='colleges',
            field=models.ManyToManyField(blank=True, to='programs.College'),
        ),
        migrations.AlterField(
            model_name='program',
            name='departments',
            field=models.ManyToManyField(blank=True, to='programs.Department'),
        ),
        migrations.AddField(
            model_name='programprofile',
            name='profile_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='programs.ProgramProfileType'),
        ),
        migrations.AddField(
            model_name='program',
            name='program_profiles',
            field=models.ManyToManyField(to='programs.ProgramProfile'),
        ),
    ]
