from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0022_rename_reference_mask_kitproducto_clave_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='kit',
            name='cantidad',
            field=models.IntegerField(default=1, help_text='Cantidad de unidades del kit'),
        ),
    ]
