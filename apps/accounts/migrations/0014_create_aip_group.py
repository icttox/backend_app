from django.db import migrations
from django.contrib.auth.models import Group, Permission


def create_aip_group(apps, schema_editor):
    # Crear el grupo AIP si no existe
    group, created = Group.objects.get_or_create(name='AIP')
    if created:
        print(f"Grupo 'AIP' creado exitosamente")
    else:
        print(f"El grupo 'AIP' ya existía")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_userprofile_categorias_compras_asignadas_and_more'),  # Dependencia ajustada a la u00faltima migraciu00f3n
    ]

    operations = [
        migrations.RunPython(create_aip_group),
    ]
