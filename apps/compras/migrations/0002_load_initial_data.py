from django.db import migrations

def load_initial_data(apps, schema_editor):
    CategoriaComprador = apps.get_model('compras', 'CategoriaComprador')
    
    # Initial data mapping compradores to categorias
    initial_data = [
        {"comprador": "DIANA", "categoria_id": 71},
        {"comprador": "DIANA", "categoria_id": 107},
        {"comprador": "DIANA", "categoria_id": 69},
        {"comprador": "DIANA", "categoria_id": 78},
        {"comprador": "DIANA", "categoria_id": 109},
        {"comprador": "DIANA", "categoria_id": 102},
        {"comprador": "DIANA", "categoria_id": 65},
        {"comprador": "ANTONIO", "categoria_id": 95},
        {"comprador": "ANTONIO", "categoria_id": 64},
        {"comprador": "ANTONIO", "categoria_id": 66},
        {"comprador": "ANTONIO", "categoria_id": 121},
        {"comprador": "ANTONIO", "categoria_id": 82},
        {"comprador": "ANTONIO", "categoria_id": 124},
        {"comprador": "ANTONIO", "categoria_id": 111},
        {"comprador": "ANTONIO", "categoria_id": 99},
        {"comprador": "ANTONIO", "categoria_id": 103},
        {"comprador": "ANTONIO", "categoria_id": 93},
        {"comprador": "KATIA", "categoria_id": 67},
        {"comprador": "KATIA", "categoria_id": 79},
        {"comprador": "KATIA", "categoria_id": 100},
        {"comprador": "KATIA", "categoria_id": 85},
        {"comprador": "EDUARDO", "categoria_id": 84},
        {"comprador": "EDUARDO", "categoria_id": 63},
        {"comprador": "EDUARDO", "categoria_id": 104},
        {"comprador": "EDUARDO", "categoria_id": 84},  # Note: This is a duplicate of an earlier entry
        {"comprador": "EDUARDO", "categoria_id": 83},
        {"comprador": "EDUARDO", "categoria_id": 90},
        {"comprador": "EDUARDO", "categoria_id": 110},
        {"comprador": "EDUARDO", "categoria_id": 68},
        {"comprador": "EDUARDO", "categoria_id": 77},
        {"comprador": "EDUARDO", "categoria_id": 80},
    ]
    
    # Create all CategoriaComprador instances
    for data in initial_data:
        CategoriaComprador.objects.get_or_create(
            categoria_id=data['categoria_id'],
            defaults={
                'comprador': data['comprador'],
                'activo': True
            }
        )
        
class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
