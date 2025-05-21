from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0025_add_usuario_fields_to_cotizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='productocotizacion',
            name='producto_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='kitproducto',
            name='producto_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
