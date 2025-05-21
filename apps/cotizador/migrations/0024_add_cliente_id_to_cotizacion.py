from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0023_add_cantidad_to_kit'),
    ]

    operations = [
        migrations.AddField(
            model_name='cotizacion',
            name='cliente_id',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
