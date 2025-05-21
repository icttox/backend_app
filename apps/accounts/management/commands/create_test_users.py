from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.accounts.models import User, Unidad

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con diferentes roles'

    def handle(self, *args, **options):
        # Crear una sucursal de prueba
        sucursal, _ = Unidad.objects.get_or_create(
            nombre_corto='Sucursal Test',
            defaults={
                'razon_social': 'GPF',  # Asegúrate que este valor existe en RAZON_SOCIAL_CHOICES
                'tipo': 'PROPIA',       # Asegúrate que este valor existe en TIPO_UNIDAD_CHOICES
                'nombre_cliente_final': 'Cliente Test',
                'rfc_cliente_final': 'TEST010101XX1',
                'id_pricelist': 1
            }
        )

        # Crear usuarios de prueba para cada rol
        usuarios_test = [
            {
                'email': 'admin@test.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'Test',
                'role': 'Administrador',
                'unidad': None  # Admin puede ver todas las sucursales
            },
            {
                'email': 'gerente@test.com',
                'password': 'gerente123',
                'first_name': 'Gerente',
                'last_name': 'Ventas',
                'role': 'Gerente de Ventas',
                'unidad': None  # Gerente puede ver todas las sucursales
            },
            {
                'email': 'lider@test.com',
                'password': 'lider123',
                'first_name': 'Líder',
                'last_name': 'Sucursal',
                'role': 'Líder de Sucursal',
                'unidad': sucursal
            },
            {
                'email': 'vendedor@test.com',
                'password': 'vendedor123',
                'first_name': 'Vendedor',
                'last_name': 'Test',
                'role': 'Vendedor',
                'unidad': sucursal
            },
            {
                'email': 'backoffice@test.com',
                'password': 'back123',
                'first_name': 'Back',
                'last_name': 'Office',
                'role': 'Backoffice',
                'unidad': None  # Backoffice puede ver todas las sucursales
            },
        ]

        for user_data in usuarios_test:
            try:
                # Crear usuario si no existe
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'unidad': user_data['unidad']
                    }
                )
                
                if created:
                    user.set_password(user_data['password'])
                    # Hacer superusuario al admin
                    if user_data['role'] == 'Administrador':
                        user.is_staff = True
                        user.is_superuser = True
                    user.save()
                
                # Asignar rol (grupo)
                group = Group.objects.get(name=user_data['role'])
                user.groups.clear()
                user.groups.add(group)
                
                status = 'creado' if created else 'actualizado'
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario {user.email} {status} con rol {user_data["role"]}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando usuario {user_data["email"]}: {str(e)}')
                )
