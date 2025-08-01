# Generated by Django 5.0.1 on 2025-02-21 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0008_cotizacion_fecha_aprobacion_cotizacion_fecha_envio_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cotizacion',
            name='cliente',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='email_cliente',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='email_vendedor',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='folio',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='motivo',
            field=models.TextField(blank=True, default='', help_text='Motivo de rechazo o cancelación'),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='persona_contacto',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='proyectista',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='proyecto',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='telefono_cliente',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='telefono_vendedor',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='unidad_facturacion',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='vendedor',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
