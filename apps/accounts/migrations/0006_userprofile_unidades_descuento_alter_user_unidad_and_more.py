# Generated by Django 5.0.1 on 2025-02-18 18:08

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_userprofile_unidades'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='unidades_descuento',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('CDMX', 'CDMX'), ('QRO', 'Querétaro'), ('LAG', 'Laguna'), ('MTY', 'Monterrey'), ('SPL', 'SPL'), ('GDL', 'Guadalajara'), ('PUE', 'Puebla')], max_length=4), blank=True, help_text='Unidades de descuento asignadas al usuario para el manejo de precios', null=True, size=None),
        ),
        migrations.AlterField(
            model_name='user',
            name='unidad',
            field=models.CharField(blank=True, choices=[(32, 32), (33, 33), (34, 34), (40, 40), (43, 43)], max_length=10, null=True, verbose_name='Unidad'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='failed_login_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_failed_login',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_password_change',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='require_password_change',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='unidades',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(32, 'Monterrey'), (33, 'SPL'), (34, 'Querétaro'), (40, 'Laguna'), (43, 'CDMX')]), blank=True, help_text='Unidades administrativas a las que pertenece el usuario', null=True, size=None),
        ),
    ]
