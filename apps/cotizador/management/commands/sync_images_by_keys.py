from django.core.management.base import BaseCommand
from supabase import create_client, Client
import os
import logging
from apps.cotizador.models import CotizadorImagenproducto
from apps.cotizador.cache.models import ProductsCache
from django.db.models import Q
import json
from tqdm import tqdm

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Busca imu00e1genes en Supabase Storage para un conjunto especu00edfico de claves de productos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keys-file',
            type=str,
            help='Ruta al archivo JSON con las claves de productos',
        )
        parser.add_argument(
            '--keys',
            nargs='+',
            type=str,
            help='Lista de claves de productos separadas por espacios',
        )
        parser.add_argument(
            '--update-cache',
            action='store_true',
            dest='update_cache',
            default=True,
            help='Actualizar tambiu00e9n la tabla ProductsCache',
        )
        parser.add_argument(
            '--recursive',
            action='store_true',
            dest='recursive',
            default=True,
            help='Buscar imu00e1genes recursivamente en subcarpetas',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Mostrar informaciu00f3n detallada del proceso',
        )

    def handle(self, *args, **options):
        SUPABASE_URL = "https://wlwxbdlmrcgjzmnjovbm.supabase.co"
        SUPABASE_KEY = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indsd3hiZGxtcmNnanptbmpvdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTM4MjI1MSwiZXhwIjoyMDU0OTU4MjUxfQ.QgMuPGN3I3WDv5G7nYK5DR23eiyBZfbf_tn2ZjxhCa8"
        )
        BUCKET_NAME = "imagenes-productos"
        update_cache = options['update_cache']
        recursive = options['recursive']
        verbose = options['verbose']
        
        # Obtener las claves de productos
        product_keys = []
        
        # Opciu00f3n 1: Desde un archivo JSON
        if options.get('keys_file'):
            try:
                with open(options['keys_file'], 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        product_keys = data
                    elif isinstance(data, dict) and 'keys' in data:
                        product_keys = data['keys']
                    else:
                        self.stdout.write(self.style.ERROR(f"Formato de archivo JSON no vu00e1lido. Debe ser una lista o un diccionario con la clave 'keys'"))
                        return
                    
                    # Eliminar duplicados y valores vacu00edos
                    product_keys = [key for key in product_keys if key and key.strip()]
                    product_keys = list(set(product_keys))  # Eliminar duplicados
                    
                    self.stdout.write(f"Se cargaron {len(product_keys)} claves u00fanicas desde el archivo JSON")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al leer el archivo JSON: {str(e)}"))
                return
        
        # Opciu00f3n 2: Desde la lu00ednea de comandos
        elif options.get('keys'):
            product_keys = options['keys']
            # Eliminar duplicados y valores vacu00edos
            product_keys = [key for key in product_keys if key and key.strip()]
            product_keys = list(set(product_keys))  # Eliminar duplicados
        
        # Verificar que tengamos claves para procesar
        if not product_keys:
            self.stdout.write(self.style.ERROR("No se proporcionaron claves de productos. Use --keys o --keys-file"))
            return
        
        self.stdout.write(f"Procesando {len(product_keys)} claves de productos")
        
        # Contadores para estadu00edsticas
        encontrados = 0
        no_encontrados = 0
        actualizados = 0
        errores = 0
        
        try:
            # Conectar a Supabase
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.stdout.write(self.style.SUCCESS(f"Conexiu00f3n exitosa a Supabase"))
            
            # Diccionario para almacenar todas las rutas de archivos encontradas
            all_files = {}
            
            # Listar todos los archivos en el bucket (con recursividad si se solicita)
            self.stdout.write("Obteniendo lista de archivos en Supabase Storage...")
            self.obtener_todos_archivos(supabase, BUCKET_NAME, "", all_files, recursive)
            self.stdout.write(f"Total de archivos encontrados en storage: {len(all_files)}")
            
            # Guardar las claves procesadas para verificaciu00f3n
            processed_keys = []
            
            # Procesar cada clave de producto
            with tqdm(total=len(product_keys), desc="Procesando claves") as pbar:
                for key in product_keys:
                    pbar.update(1)
                    processed_keys.append(key)
                    try:
                        # Buscar archivos que coincidan con la clave
                        matches = self.buscar_coincidencias(key, all_files)
                        
                        if matches:
                            # Tomar el primer match como la URL a guardar
                            file_path = matches[0]
                            url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
                            
                            # Actualizar o crear registro en CotizadorImagenproducto
                            imagen, created = CotizadorImagenproducto.objects.update_or_create(
                                clave_padre=key,
                                defaults={'url': url}
                            )
                            
                            # Actualizar ProductsCache si se solicita
                            if update_cache:
                                productos_actualizados = ProductsCache.objects.filter(reference_mask=key).update(image_url=url)
                                actualizados += productos_actualizados
                            
                            encontrados += 1
                            if verbose:
                                self.stdout.write(f"Imagen encontrada para {key}: {url}")
                        else:
                            no_encontrados += 1
                            if verbose:
                                self.stdout.write(f"No se encontru00f3 imagen para {key}")
                    
                    except Exception as e:
                        errores += 1
                        self.stdout.write(self.style.ERROR(f"Error al procesar clave {key}: {str(e)}"))
                        logger.error(f"Error al procesar clave {key}: {str(e)}")
            
            # Verificar que todas las claves fueron procesadas
            if len(processed_keys) != len(product_keys):
                self.stdout.write(self.style.WARNING(
                    f"ADVERTENCIA: Se procesaron {len(processed_keys)} claves de las {len(product_keys)} proporcionadas"
                ))
                # Mostrar las claves que no se procesaron
                missing_keys = set(product_keys) - set(processed_keys)
                if missing_keys:
                    self.stdout.write("Claves no procesadas:")
                    for key in missing_keys:
                        self.stdout.write(f"  - {key}")
            
            # Mostrar resumen
            self.stdout.write(self.style.SUCCESS(
                f"\nProceso completado:\n"
                f"- Total de claves proporcionadas: {len(product_keys)}\n"
                f"- Total de claves procesadas: {len(processed_keys)}\n"
                f"- Imu00e1genes encontradas: {encontrados}\n"
                f"- Imu00e1genes no encontradas: {no_encontrados}\n"
                f"- Productos actualizados en cache: {actualizados}\n"
                f"- Errores: {errores}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al conectar con Supabase: {str(e)}"))
            logger.error(f"Error al conectar con Supabase: {str(e)}")
    
    def obtener_todos_archivos(self, supabase, bucket_name, ruta_actual, all_files, recursive):
        """Obtiene recursivamente todos los archivos en el bucket"""
        try:
            # Listar contenido de la carpeta actual
            response = supabase.storage.from_(bucket_name).list(ruta_actual)
            
            for item in response:
                nombre_item = item["name"]
                es_carpeta = item.get("id") is None
                
                # Construir la ruta completa para el elemento actual
                if ruta_actual:
                    ruta_completa = f"{ruta_actual}/{nombre_item}"
                else:
                    ruta_completa = nombre_item
                
                # Si es carpeta y recursive=True, procesarla recursivamente
                if es_carpeta and recursive:
                    self.obtener_todos_archivos(supabase, bucket_name, ruta_completa, all_files, recursive)
                # Si es archivo, agregarlo al diccionario
                elif not es_carpeta:
                    # Extraer el nombre base del archivo sin extensiu00f3n
                    nombre_base = os.path.splitext(nombre_item)[0]
                    # Guardar la ruta completa en el diccionario
                    all_files[nombre_base.lower()] = ruta_completa
                    
                    # Tambiu00e9n guardar una versiu00f3n sin prefijos de carpeta para bu00fasquedas alternativas
                    if '/' in ruta_completa:
                        nombre_archivo = ruta_completa.split('/')[-1]
                        nombre_base_archivo = os.path.splitext(nombre_archivo)[0]
                        if nombre_base_archivo.lower() not in all_files:
                            all_files[nombre_base_archivo.lower()] = ruta_completa
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al listar contenido de {ruta_actual}: {str(e)}"))
            logger.error(f"Error al listar contenido de {ruta_actual}: {str(e)}")
    
    def buscar_coincidencias(self, key, all_files):
        """Busca archivos que coincidan con la clave del producto"""
        matches = []
        
        # Normalizar la clave para bu00fasqueda
        key_lower = key.lower()
        
        # Buscar coincidencia exacta primero
        if key_lower in all_files:
            matches.append(all_files[key_lower])
            return matches  # Si hay coincidencia exacta, devolver inmediatamente
        
        # Buscar coincidencias parciales si no hay coincidencia exacta
        for file_key, file_path in all_files.items():
            # Verificar si la clave estu00e1 contenida en el nombre del archivo
            if key_lower in file_key or file_key in key_lower:
                matches.append(file_path)
                # No salir del bucle para encontrar todas las coincidencias posibles
        
        return matches
