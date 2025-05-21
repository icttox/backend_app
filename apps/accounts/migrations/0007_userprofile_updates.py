from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_userprofile_unidades_descuento_alter_user_unidad_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='unidades_descuento',
            field=ArrayField(
                base_field=models.CharField(choices=[('CDMX', 'CDMX'), ('QRO', 'Querétaro'), ('LAG', 'Laguna'), ('MTY', 'Monterrey'), ('SPL', 'SPL'), ('GDL', 'Guadalajara'), ('PUE', 'Puebla')], max_length=4),
                blank=True,
                default=list,
                null=True,
                help_text='Unidades de descuento asignadas al usuario para el manejo de precios'
            ),
        ),
    ]
