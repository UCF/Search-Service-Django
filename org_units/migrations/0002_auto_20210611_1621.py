# Generated by Django 3.1.1 on 2021-06-11 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('org_units', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentUnit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationUnit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='organization',
            name='college',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='teledata',
        ),
        migrations.DeleteModel(
            name='Department',
        ),
        migrations.DeleteModel(
            name='Organization',
        ),
        migrations.AddField(
            model_name='departmentunit',
            name='organization_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='org_units.organizationunit'),
        ),
    ]