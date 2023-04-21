# Generated by Django 4.1.7 on 2023-03-17 05:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('dns', models.CharField(max_length=255)),
                ('record', models.CharField(max_length=255)),
                ('gslb_health', models.CharField(max_length=255, null=True)),
                ('gtm_health', models.CharField(max_length=255, null=True)),
                ('vs_health', models.CharField(max_length=255, null=True)),
                ('update_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='DomainTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domainId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='zoneManager.domain')),
                ('tagId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='zoneManager.tag')),
            ],
        ),
        migrations.AddField(
            model_name='domain',
            name='tag',
            field=models.ManyToManyField(through='zoneManager.DomainTag', to='zoneManager.tag'),
        ),
    ]
