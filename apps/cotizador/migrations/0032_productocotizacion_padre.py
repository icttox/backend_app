# Generated by Django 5.0.1 on 2025-03-27 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0031_merge_20250327_0230'),
    ]

    operations = [
        migrations.AddField(
            model_name='productocotizacion',
            name='padre',
            field=models.BooleanField(default=False),
        ),
    ]
