# Generated by Django 5.0.1 on 2025-03-17 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0026_add_producto_id_to_models'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cliente',
            options={'verbose_name': 'Cliente', 'verbose_name_plural': 'Clientes'},
        ),
        migrations.AlterModelOptions(
            name='producttemplate',
            options={'managed': False},
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='direccion',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='email',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='empresa',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='id',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='nombre',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='telefono',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='cliente',
            name='name_partner',
            field=models.CharField(blank=True, help_text='Nombre del cliente', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='cliente',
            name='partner_id',
            field=models.IntegerField(default='', help_text='ID único del cliente', primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cliente',
            name='rfc',
            field=models.CharField(blank=True, help_text='RFC del cliente', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='kit',
            name='tag',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='kitproducto',
            name='tag',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddIndex(
            model_name='cliente',
            index=models.Index(fields=['name_partner'], name='idx_cliente_name'),
        ),
        migrations.AddIndex(
            model_name='cliente',
            index=models.Index(fields=['rfc'], name='idx_cliente_rfc'),
        ),
        migrations.AlterModelTable(
            name='cliente',
            table='cotizador_cliente',
        ),
    ]
