# Generated by Django 3.1.1 on 2021-04-26 18:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('teledata', '0014_auto_20200922_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orcid_id', models.CharField(max_length=19, unique=True)),
                ('teledata_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='researcher_records', to='teledata.staff')),
            ],
        ),
    ]