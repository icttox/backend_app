# Generated by Django 5.0.1 on 2025-04-25 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0040_cotizacion_hs_deal_id_kitproducto_route_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cotizacion',
            name='hs_deal_id',
            field=models.CharField(blank=True, help_text='ID del negocio en HubSpot', max_length=50, null=True),
        ),
    ]
