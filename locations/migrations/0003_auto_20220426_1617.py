# Generated by Django 3.2.4 on 2022-04-26 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0002_auto_20220426_1613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facility',
            name='abbreviation',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='parkinglot',
            name='abbreviation',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]