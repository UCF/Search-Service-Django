# Generated by Django 3.1.1 on 2021-04-28 18:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='biography',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ResearchWork',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1000)),
                ('subtitle', models.CharField(blank=True, max_length=1000, null=True)),
                ('abstract', models.TextField(blank=True, null=True)),
                ('publish_date', models.DateField()),
                ('work_type', models.CharField(max_length=255)),
                ('work_put_code', models.IntegerField(help_text='Primary key within ORCID work records. Uniquely identified the work within their system.', unique=True)),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='works', to='research.researcher')),
            ],
        ),
        migrations.CreateModel(
            name='ResearcherEducation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institution_name', models.CharField(max_length=255)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('department_name', models.CharField(blank=True, max_length=255, null=True)),
                ('role_name', models.CharField(max_length=255)),
                ('education_put_code', models.IntegerField(help_text='Primary key within ORCID education records. Uniquely identified the educational record within their system.', unique=True)),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education', to='research.researcher')),
            ],
        ),
    ]