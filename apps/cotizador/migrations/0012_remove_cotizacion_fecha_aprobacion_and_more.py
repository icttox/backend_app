# Generated by Django 5.0.1 on 2025-02-21 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0011_cotizacion_condiciones_pago_cotizacion_mostrar_clave_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cotizacion',
            name='fecha_aprobacion',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='fecha_envio',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='fecha_rechazo',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='usuario_aprobacion',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='usuario_creacion',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='usuario_envio',
        ),
        migrations.RemoveField(
            model_name='cotizacion',
            name='usuario_rechazo',
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='motivo',
            field=models.TextField(blank=True, default=''),
        ),
    ]
