# Generated by Django 3.2.8 on 2022-01-04 17:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0050_auto_20220104_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='start_term',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='start_term_programs', to='programs.academicterm'),
        ),
    ]
