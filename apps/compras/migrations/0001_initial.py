from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaComprador',
            fields=[
                ('categoria_id', models.IntegerField(help_text='ID de la categoría de productos', primary_key=True, serialize=False)),
                ('comprador', models.CharField(choices=[('DIANA', 'Diana'), ('ANTONIO', 'Antonio'), ('KATIA', 'Katia'), ('EDUARDO', 'Eduardo')], help_text='Nombre del comprador asignado a esta categoría', max_length=50)),
                ('nombre_categoria', models.CharField(blank=True, help_text='Nombre descriptivo de la categoría', max_length=100, null=True)),
                ('descripcion', models.TextField(blank=True, help_text='Descripción detallada de la categoría', null=True)),
                ('activo', models.BooleanField(default=True, help_text='Indica si la categoría está activa')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Categoría de Comprador',
                'verbose_name_plural': 'Categorías de Compradores',
                'ordering': ['categoria_id'],
            },
        ),
        migrations.CreateModel(
            name='CompradorUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_comprador', models.CharField(choices=[('DIANA', 'Diana'), ('ANTONIO', 'Antonio'), ('KATIA', 'Katia'), ('EDUARDO', 'Eduardo')], help_text='Nombre del comprador que identifica al usuario', max_length=50)),
                ('activo', models.BooleanField(default=True, help_text='Indica si el comprador está activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(help_text='Usuario del sistema asociado al comprador', on_delete=models.deletion.CASCADE, related_name='comprador_profile', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Usuario Comprador',
                'verbose_name_plural': 'Usuarios Compradores',
                'ordering': ['nombre_comprador'],
            },
        ),
    ]
