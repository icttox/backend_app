from django.core.management.base import BaseCommand
from apps.cotizador.models import CotizadorImagenproducto
from apps.cotizador.cache.models import ProductsCache
from django.db.models import F
from django.utils import timezone
import logging
import requests
from django.db import transaction
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza las URLs de las imágenes con la tabla products_cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamaño del lote para procesar productos',
        )
        parser.add_argument(
            '--validate-urls',
            action='store_true',
            dest='validate_urls',
            default=False,
            help='Validar que las URLs sean accesibles',
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help='Forzar actualización incluso si la URL no ha cambiado',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        validate_urls = options['validate_urls']
        force_update = options['force_update']

        # Contadores para estadísticas
        total_productos = 0
        total_actualizados = 0
        total_sin_cambios = 0
        total_errores = 0
        total_sin_imagen = 0

        try:
            # Obtener todos los productos en cache
            productos = ProductsCache.objects.all()
            total_productos = productos.count()
            self.stdout.write(f"Total de productos en cache: {total_productos}")

            # Procesar productos en lotes para mejor rendimiento
            offset = 0
            with tqdm(total=total_productos, desc="Sincronizando productos") as pbar:
                while offset < total_productos:
                    # Obtener lote actual
                    lote_productos = productos[offset:offset+batch_size]
                    
                    # Procesar cada producto en el lote
                    for producto in lote_productos:
                        try:
                            # Buscar imagen correspondiente al código del producto
                            imagen = CotizadorImagenproducto.objects.filter(clave_padre__iexact=producto.reference_mask).first()
                            if not imagen:
                                imagen = CotizadorImagenproducto.objects.filter(clave_padre__icontains=producto.reference_mask).first()
                            
                            if imagen:
                                url_anterior = producto.image_url or ""
                                nueva_url = imagen.url
                                
                                # Validar URL si se solicitó
                                url_valida = True
                                if validate_urls and nueva_url:
                                    try:
                                        response = requests.head(nueva_url, timeout=5)
                                        url_valida = response.status_code == 200
                                        if not url_valida:
                                            self.stdout.write(self.style.WARNING(
                                                f"URL no válida para {producto.reference_mask}: {nueva_url} "
                                                f"(Status: {response.status_code})"
                                            ))
                                    except Exception as e:
                                        url_valida = False
                                        self.stdout.write(self.style.WARNING(
                                            f"Error al validar URL para {producto.reference_mask}: {str(e)}"
                                        ))
                                
                                # Actualizar URL si ha cambiado o si se fuerza la actualización
                                if url_valida and (force_update or url_anterior != nueva_url):
                                    # Guardar URL anterior para registro
                                    url_anterior_log = url_anterior if url_anterior else "[Sin URL]"
                                    
                                    # Actualizar producto
                                    producto.image_url = nueva_url
                                    producto.save(update_fields=['image_url'])
                                    
                                    total_actualizados += 1
                                    self.stdout.write(
                                        f"Actualizado: {producto.reference_mask} - "
                                        f"URL anterior: {url_anterior_log} -> "
                                        f"Nueva URL: {nueva_url}"
                                    )
                                else:
                                    total_sin_cambios += 1
                            else:
                                total_sin_imagen += 1
                                if producto.image_url:  # Si tenía URL pero ya no hay imagen
                                    self.stdout.write(self.style.WARNING(
                                        f"Producto sin imagen pero con URL: {producto.reference_mask} - {producto.image_url}"
                                    ))
                                    # Opcionalmente, se podría limpiar la URL aquí
                                    # producto.image_url = None
                                    # producto.save(update_fields=['image_url'])
                        except Exception as e:
                            total_errores += 1
                            self.stdout.write(self.style.ERROR(
                                f"Error al procesar producto {producto.reference_mask}: {str(e)}"
                            ))
                            logger.error(f"Error al procesar producto {producto.reference_mask}: {str(e)}")
                    
                    # Actualizar offset y barra de progreso
                    offset += batch_size
                    pbar.update(len(lote_productos))
                    
                    # Pequeña pausa para no sobrecargar la base de datos
                    time.sleep(0.01)

            # Mostrar estadísticas finales
            self.stdout.write(self.style.SUCCESS(f"\nSincronización completada:"))
            self.stdout.write(f"- Total de productos procesados: {total_productos}")
            self.stdout.write(f"- Productos actualizados: {total_actualizados}")
            self.stdout.write(f"- Productos sin cambios: {total_sin_cambios}")
            self.stdout.write(f"- Productos sin imagen: {total_sin_imagen}")
            self.stdout.write(f"- Errores: {total_errores}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error general: {str(e)}"))
            logger.error(f"Error general: {str(e)}")
