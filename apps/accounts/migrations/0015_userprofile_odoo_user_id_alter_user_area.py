# Generated by Django 5.0.1 on 2025-05-14 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_create_aip_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='odoo_user_id',
            field=models.IntegerField(blank=True, help_text='ID de usuario en Odoo para usuarios del área de compras', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='area',
            field=models.CharField(blank=True, choices=[('RH', 'Recursos Humanos'), ('VENTAS', 'Ventas'), ('COMPRAS', 'Compras'), ('PROD', 'Producción'), ('TI', 'Tecnología'), ('AIP', 'AIP')], max_length=20, null=True),
        ),
    ]
