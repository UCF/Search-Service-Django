# Generated by Django 3.2.20 on 2024-07-17 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0058_auto_20240304_1853'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='highlights',
            field=models.JSONField(null=True),
        ),
    ]