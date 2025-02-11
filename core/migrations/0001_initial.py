# Generated by Django 3.2.20 on 2023-11-08 13:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    def create_extendeduser_records(apps, schema_editor):
        ExtendedUser = apps.get_model('core', 'ExtendedUser')
        User = apps.get_model('auth', 'User')

        users = User.objects.all()

        for user in users:
            extended_user = ExtendedUser.objects.create(user=user)
            extended_user.save()


    dependencies = [
        migrations.swappable_dependency('programs.College'),
        migrations.swappable_dependency('programs.Department'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtendedUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('colleges_can_edit', models.ManyToManyField(related_name='editors', to='programs.College')),
                ('departments_can_edit', models.ManyToManyField(related_name='editors', to='programs.Department')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(create_extendeduser_records)
    ]
