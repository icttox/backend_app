from django.core.management.base import BaseCommand
from apps.accounts.roles import setup_roles

class Command(BaseCommand):
    help = 'Configura los roles iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando roles y permisos...')
        try:
            setup_roles()
            self.stdout.write(self.style.SUCCESS('Roles y permisos configurados exitosamente'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al configurar roles: {str(e)}')
            )
