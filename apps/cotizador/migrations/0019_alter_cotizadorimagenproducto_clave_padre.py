# Generated by Django 5.0.1 on 2025-03-04 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0018_alter_cotizadorimagenproducto_clave_padre'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cotizadorimagenproducto',
            name='clave_padre',
            field=models.CharField(db_index=True, help_text='Clave del producto que coincide con reference_mask de ProductTemplate', max_length=255, unique=True),
        ),
    ]
