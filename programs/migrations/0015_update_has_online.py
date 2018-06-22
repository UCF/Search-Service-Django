from django.db import migrations
from programs.models import Program

def update_has_online(apps, schema_editor):
    programs = Program.objects.all()

    for program in programs:
        program.save()

class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0014_program_has_online'),
    ]

    operations = [
        migrations.RunPython(update_has_online),
    ]
