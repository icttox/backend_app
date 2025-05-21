from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime
import logging
from ...cache.sync import sync_products_to_supabase

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza los productos desde la copia de Odoo directamente a Supabase'

    def handle(self, *args, **options):
        start_time = datetime.now()
        logger.info(f"Iniciando sincronización de productos con Supabase: {start_time}")
        
        try:
            # Llamar directamente a la función de sincronización con Supabase
            self.stdout.write("Iniciando sincronización de productos con Supabase...")
            result = sync_products_to_supabase()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Sincronización completada en {duration}")
            logger.info(f"Total de productos: {result.get('total', 0)}")
            logger.info(f"Productos sincronizados: {result.get('successful', 0)}")
            logger.info(f"Productos con imágenes: {result.get('with_images', 0)}")
            logger.info(f"Productos sin imágenes: {result.get('without_images', 0)}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sincronización exitosa con Supabase:\n'
                    f'- Total de productos: {result.get("total", 0)}\n'
                    f'- Productos sincronizados: {result.get("successful", 0)}\n'
                    f'- Productos con imágenes: {result.get("with_images", 0)}\n'
                    f'- Productos sin imágenes: {result.get("without_images", 0)}\n'
                    f'- Duración: {duration}'
                )
            )
            
        except Exception as e:
            logger.error(f"Error durante la sincronización: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error durante la sincronización: {str(e)}')
            )
            raise
