# Generated by Django 3.2.25 on 2025-02-27 13:40

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0005_auto_20220424_2025'),
        ('marketing', '0002_rename_speaker_quote_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='quote',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='tags'),
        ),
    ]
