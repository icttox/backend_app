from django.core.management.base import BaseCommand
from supabase import create_client, Client
import os
import logging
from apps.cotizador.models import CotizadorImagenproducto

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza las URLs de imágenes desde Supabase Storage a la tabla cotizador_imagenproducto.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recursive',
            action='store_true',
            dest='recursive',
            default=True,
            help='Buscar imágenes recursivamente en subcarpetas',
        )

    def handle(self, *args, **options):
        SUPABASE_URL = "https://wlwxbdlmrcgjzmnjovbm.supabase.co"
        SUPABASE_KEY = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indsd3hiZGxtcmNnanptbmpvdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTM4MjI1MSwiZXhwIjoyMDU0OTU4MjUxfQ.QgMuPGN3I3WDv5G7nYK5DR23eiyBZfbf_tn2ZjxhCa8"
        )
        BUCKET_NAME = "imagenes-productos"
        recursive = options['recursive']

        # Contadores para estadísticas
        total_archivos = 0
        actualizados = 0
        creados = 0
        ignorados = 0
        errores = 0

        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.stdout.write(self.style.SUCCESS(f"Conexión exitosa a Supabase"))

            # Procesar carpetas y archivos
            self.stdout.write("Listando contenido del bucket...")
            self.procesar_carpeta(supabase, SUPABASE_URL, BUCKET_NAME, "", recursive, 
                                  total_archivos, actualizados, creados, ignorados, errores)

            # Mostrar resumen
            self.stdout.write(self.style.SUCCESS(
                f"\nSincronización completada:\n"
                f"- Total de archivos procesados: {total_archivos}\n"
                f"- Registros actualizados: {actualizados}\n"
                f"- Registros creados: {creados}\n"
                f"- Archivos ignorados: {ignorados}\n"
                f"- Errores: {errores}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al conectar con Supabase: {str(e)}"))
            logger.error(f"Error al conectar con Supabase: {str(e)}")

    def procesar_carpeta(self, supabase, supabase_url, bucket_name, ruta_actual, recursive, 
                         total_archivos, actualizados, creados, ignorados, errores):
        try:
            # Listar contenido de la carpeta actual con paginación
            self.stdout.write(f"Listando contenido de {ruta_actual or '[Raíz]'}...")
            contenido = self.listar_contenido_con_paginacion(supabase, bucket_name, ruta_actual)
            self.stdout.write(f"Total de elementos encontrados en {ruta_actual or '[Raíz]'}: {len(contenido)}")

            # Procesar cada elemento (archivo o carpeta)
            for item in contenido:
                nombre_item = item["name"]
                es_carpeta = item.get("id") is None
                
                # Construir la ruta completa para el elemento actual
                if ruta_actual:
                    ruta_completa = f"{ruta_actual}/{nombre_item}"
                else:
                    ruta_completa = nombre_item
                
                # Si es carpeta y recursive=True, procesarla recursivamente
                if es_carpeta and recursive:
                    self.procesar_carpeta(supabase, supabase_url, bucket_name, ruta_completa, 
                                          recursive, total_archivos, actualizados, creados, 
                                          ignorados, errores)
                # Si es archivo, procesarlo
                elif not es_carpeta:
                    self.procesar_archivo(supabase, supabase_url, bucket_name, ruta_actual, 
                                          nombre_item, total_archivos, actualizados, 
                                          creados, ignorados, errores)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al procesar carpeta {ruta_actual}: {str(e)}"))
            logger.error("Error al procesar carpeta %s: %s" % (ruta_actual, str(e)))
            errores += 1

    def listar_contenido_con_paginacion(self, supabase, bucket_name, ruta_actual):
        """Lista todo el contenido de una carpeta con paginación para superar el límite de 100 elementos"""
        todos_los_items = []
        offset = 0
        limit = 1000  # Máximo número de elementos por solicitud
        
        while True:
            try:
                # Construir opciones de paginación
                options = {
                    "limit": limit,
                    "offset": offset,
                    "sortBy": {
                        "column": "name",
                        "order": "asc"
                    }
                }
                
                # Realizar la solicitud con opciones de paginación
                if ruta_actual:
                    contenido = supabase.storage.from_(bucket_name).list(path=ruta_actual, options=options)
                else:
                    contenido = supabase.storage.from_(bucket_name).list(options=options)
                
                # Si no hay más elementos, salir del bucle
                if not contenido or len(contenido) == 0:
                    break
                    
                # Agregar elementos a la lista completa
                todos_los_items.extend(contenido)
                
                # Si recibimos menos elementos que el límite, significa que hemos terminado
                if len(contenido) < limit:
                    break
                    
                # Incrementar el offset para la siguiente solicitud
                offset += limit
                
                # Informar del progreso
                self.stdout.write(f"  Obtenidos {len(todos_los_items)} elementos de {ruta_actual or '[Raíz]'}...")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al listar contenido de {ruta_actual}: {str(e)}"))
                logger.error("Error al listar contenido de %s: %s" % (ruta_actual, str(e)))
                break
                
        return todos_los_items
            
    def procesar_archivo(self, supabase, supabase_url, bucket_name, ruta_carpeta, 
                         nombre_archivo, total_archivos, actualizados, creados, 
                         ignorados, errores):
        try:
            # Ignorar archivos placeholder
            if nombre_archivo == ".emptyFolderPlaceholder":
                ignorados += 1
                return

            total_archivos += 1
            
            # Construir la URL completa del archivo exactamente como se requiere
            # Formato: https://wlwxbdlmrcgjzmnjovbm.supabase.co/storage/v1/object/public/imagenes-productos/Almacenaje/GAA790180.png
            if ruta_carpeta:
                url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{ruta_carpeta}/{nombre_archivo}"
            else:
                url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{nombre_archivo}"
            
            # Extraer la clave_padre del nombre del archivo (sin extensión)
            # Usamos rsplit para manejar nombres con múltiples puntos, tomando solo la última extensión
            clave_padre = nombre_archivo.rsplit(".", 1)[0]
            
            self.stdout.write(f"Procesando: {nombre_archivo} en {ruta_carpeta if ruta_carpeta else 'raíz'}")
            self.stdout.write(f"  URL: {url}")
            self.stdout.write(f"  Clave padre: {clave_padre}")

            #Intentar primero una coincidencia exacta
            imagen = CotizadorImagenproducto.objects.filter(clave_padre__iexact=clave_padre).first()

            if not imagen:
                self.stdout.write(f"  No se encontró una coincidencia exacta para: {clave_padre}")
                imagen = CotizadorImagenproducto.objects.filter(clave_padre__icontains=clave_padre).first()
                if imagen:
                    self.stdout.write(f"  Coincidencia inexacta encontrada: {imagen.clave_padre}")
                    imagen.url = url
                    imagen.save()
                    self.stdout.write(f"  Actualizado registro existente para: {clave_padre}")
                    actualizados += 1
                else:
                    self.stdout.write(f"  No se encontro ninguna coincidencia para: {clave_padre}")
                    imagen = CotizadorImagenproducto(clave_padre=clave_padre, url=url)
                    imagen.save()
                    self.stdout.write(f"  Creado nuevo registro para: {clave_padre}")
                    creados += 1
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al procesar archivo {nombre_archivo}: {str(e)}"))
            logger.error("Error al procesar archivo %s: %s" % (nombre_archivo, str(e)))
            errores += 1