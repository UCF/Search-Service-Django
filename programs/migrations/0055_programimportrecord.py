# Generated by Django 3.2.20 on 2023-11-27 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0054_auto_20231120_1752'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramImportRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date_time', models.DateTimeField()),
                ('end_date_time', models.DateTimeField()),
                ('programs_processed', models.IntegerField()),
                ('programs_created', models.ManyToManyField(related_name='created_import', to='programs.Program')),
                ('programs_invalidated', models.ManyToManyField(related_name='invalidated_import', to='programs.Program')),
                ('programs_modified', models.ManyToManyField(related_name='last_modified_import', to='programs.Program')),
                ('programs_revalidated', models.ManyToManyField(related_name='revalidated_import', to='programs.Program')),
            ],
        ),
    ]
