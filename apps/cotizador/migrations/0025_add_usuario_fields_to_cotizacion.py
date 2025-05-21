from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0024_add_cliente_id_to_cotizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='cotizacion',
            name='usuario_id',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='usuario_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]
