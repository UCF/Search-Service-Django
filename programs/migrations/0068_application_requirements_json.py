from django.db import migrations, models


def copy_to_json(apps, schema_editor):
    """
    The old django-mysql field stored requirements as comma-separated
    text, and the historical model reads them back as a list.
    """
    Program = apps.get_model('programs', 'Program')
    programs = Program.objects.exclude(application_requirements=None)

    for program in programs.iterator():
        program.application_requirements_json = program.application_requirements
        program.save(update_fields=['application_requirements_json'])


def copy_from_json(apps, schema_editor):
    Program = apps.get_model('programs', 'Program')
    programs = Program.objects.exclude(application_requirements_json=None)

    for program in programs.iterator():
        program.application_requirements = program.application_requirements_json
        program.save(update_fields=['application_requirements'])


class Migration(migrations.Migration):
    """
    Moves application_requirements from django-mysql's ListTextField to
    Django's JSONField, which works on MySQL and PostgreSQL alike.

    MySQL won't change a text column to JSON in place while it holds
    values that aren't valid JSON, so the requirements go into a new
    column and the new column takes the old one's name.
    """

    dependencies = [
        ('programs', '0067_generate_college_department_slugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='application_requirements_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.RunPython(copy_to_json, copy_from_json),
        migrations.RemoveField(
            model_name='program',
            name='application_requirements',
        ),
        migrations.RenameField(
            model_name='program',
            old_name='application_requirements_json',
            new_name='application_requirements',
        ),
    ]
