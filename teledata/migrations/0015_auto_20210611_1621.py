# Generated by Django 3.1.1 on 2021-06-11 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('org_units', '0002_auto_20210611_1621'),
        ('teledata', '0014_auto_20200922_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='department_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teledata', to='org_units.departmentunit'),
        ),
        migrations.AddField(
            model_name='organization',
            name='organization_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teledata', to='org_units.organizationunit'),
        ),
    ]