from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from .models import User, Unidad
from apps.cotizador.models import Cotizacion

# Definición de roles base
ROLES = {
    'ADMIN': {
        'name': 'Administrador',
        'permissions': [
            # Permisos de usuarios
            ('add_user', User),
            ('change_user', User),
            ('delete_user', User),
            ('view_user', User),
            # Permisos de sucursales (unidades)
            ('add_unidad', Unidad),
            ('change_unidad', Unidad),
            ('delete_unidad', Unidad),
            ('view_unidad', Unidad),
            # Permisos de grupos
            ('add_group', Group),
            ('change_group', Group),
            ('delete_group', Group),
            ('view_group', Group),
            # Permisos de cotizaciones
            ('add_cotizacion', Cotizacion),
            ('change_cotizacion', Cotizacion),
            ('delete_cotizacion', Cotizacion),
            ('view_cotizacion', Cotizacion),
        ]
    },
    'GERENTE_VENTAS': {
        'name': 'Gerente de Ventas',
        'permissions': [
            # Permisos de cotizaciones
            ('add_cotizacion', Cotizacion),
            ('change_cotizacion', Cotizacion),
            ('delete_cotizacion', Cotizacion),
            ('view_cotizacion', Cotizacion),
            # Permisos de sucursales (unidades)
            ('view_unidad', Unidad),
            ('change_unidad', Unidad),
            # Permisos de usuarios (vendedores)
            ('view_user', User),
            ('change_user', User),
            # Ver grupos
            ('view_group', Group),
        ]
    },
    'LIDER_SUCURSAL': {
        'name': 'Líder de Sucursal',
        'permissions': [
            # Permisos de cotizaciones de su sucursal
            ('add_cotizacion', Cotizacion),
            ('change_cotizacion', Cotizacion),
            ('delete_cotizacion', Cotizacion),
            ('view_cotizacion', Cotizacion),
            # Permisos de su sucursal (unidad)
            ('view_unidad', Unidad),
            # Permisos de usuarios de su sucursal
            ('view_user', User),
            ('change_user', User),
            # Ver grupos
            ('view_group', Group),
        ]
    },
    'VENDEDOR': {
        'name': 'Vendedor',
        'permissions': [
            # Permisos de cotizaciones de su sucursal
            ('add_cotizacion', Cotizacion),
            ('change_cotizacion', Cotizacion),
            ('view_cotizacion', Cotizacion),
            # Ver su sucursal (unidad)
            ('view_unidad', Unidad),
        ]
    },
    'BACKOFFICE': {
        'name': 'Backoffice',
        'permissions': [
            # Permisos de cotizaciones
            ('view_cotizacion', Cotizacion),
            ('change_cotizacion', Cotizacion),
            # Ver sucursales (unidades)
            ('view_unidad', Unidad),
            # Ver usuarios
            ('view_user', User),
        ]
    }
}

def setup_roles():
    """
    Configura los roles base del sistema.
    Esta función debe ejecutarse durante la migración inicial o mediante un comando de Django.
    """
    with transaction.atomic():
        for role_key, role_data in ROLES.items():
            # Crear o actualizar el grupo
            group, _ = Group.objects.get_or_create(name=role_data['name'])
            
            # Limpiar permisos existentes
            group.permissions.clear()
            
            # Asignar nuevos permisos
            for permission_name, model_class in role_data['permissions']:
                content_type = ContentType.objects.get_for_model(model_class)
                try:
                    permission = Permission.objects.get(
                        codename=permission_name,
                        content_type=content_type,
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permiso no encontrado: {permission_name} para {model_class.__name__}")

def get_role_choices():
    """
    Retorna las opciones de roles para usar en formularios o serializadores
    """
    return [(role_data['name'], role_data['name']) for role_key, role_data in ROLES.items()]
