from django.core.management.base import BaseCommand
from apps.cotizador.cache.sync import sync_products_to_supabase

class Command(BaseCommand):
    help = 'Sincroniza productos desde PostgreSQL a Supabase'

    def handle(self, *args, **options):
        try:
            count = sync_products_to_supabase()
            self.stdout.write(
                self.style.SUCCESS(f'Sincronizados {count} productos exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al sincronizar: {str(e)}')
            )
