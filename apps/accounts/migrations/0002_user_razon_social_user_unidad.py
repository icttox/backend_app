# Generated by Django 5.0.1 on 2025-02-13 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='razon_social',
            field=models.CharField(choices=[('GEBESA_NACIONAL', 'GEBESA NACIONAL'), ('OPERADORA_SUCURSALES', 'OPERADORA DE SUCURSALES GEBESA'), ('SALMON_LAGUNA', 'SALMON DE LA LAGUNA')], default='', help_text='Razón social asociada al usuario', max_length=50, verbose_name='Razón Social'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='unidad',
            field=models.CharField(choices=[('CDMX', 'CDMX'), ('QRO', 'Querétaro'), ('LAG', 'Laguna'), ('MTY', 'Monterrey'), ('SPL', 'SPL'), ('GDL', 'Guadalajara')], default='', help_text='Unidad a la que pertenece el usuario', max_length=20, verbose_name='Unidad'),
            preserve_default=False,
        ),
    ]
