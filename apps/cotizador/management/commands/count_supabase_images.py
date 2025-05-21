from django.core.management.base import BaseCommand
from supabase import create_client, Client
import os
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Contabiliza el número de imágenes en el storage de Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recursive',
            action='store_true',
            dest='recursive',
            default=True,
            help='Buscar imágenes recursivamente en subcarpetas',
        )
        parser.add_argument(
            '--detail',
            action='store_true',
            dest='detail',
            default=False,
            help='Mostrar detalle de archivos por carpeta',
        )
        parser.add_argument(
            '--all-files',
            action='store_true',
            dest='all_files',
            default=True,
            help='Contar todos los archivos, no solo imágenes',
        )
        parser.add_argument(
            '--find-duplicates',
            action='store_true',
            dest='find_duplicates',
            default=False,
            help='Buscar archivos con nombres duplicados o similares basados en claves de producto',
        )

    def handle(self, *args, **options):
        SUPABASE_URL = "https://wlwxbdlmrcgjzmnjovbm.supabase.co"
        SUPABASE_KEY = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indsd3hiZGxtcmNnanptbmpvdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTM4MjI1MSwiZXhwIjoyMDU0OTU4MjUxfQ.QgMuPGN3I3WDv5G7nYK5DR23eiyBZfbf_tn2ZjxhCa8"
        )
        BUCKET_NAME = "imagenes-productos"
        recursive = options['recursive']
        show_detail = options['detail']
        all_files = options['all_files']
        find_duplicates = options['find_duplicates']

        # Contadores y estructuras de datos
        total_archivos = 0
        total_carpetas = 0
        archivos_por_carpeta = defaultdict(int)
        archivos_por_extension = defaultdict(int)
        lista_archivos = defaultdict(list)
        archivos_placeholder = 0
        # Estructura para almacenar archivos similares basados en claves de producto
        archivos_similares = defaultdict(list)

        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.stdout.write(self.style.SUCCESS(f"Conexión exitosa a Supabase"))

            # Iniciar conteo
            self.stdout.write("Contabilizando todos los archivos en el bucket...")
            
            # Llamar al método de conteo y capturar los resultados
            resultados = self.contar_archivos_recursivo(supabase, BUCKET_NAME, "", recursive, all_files, show_detail, find_duplicates)
            
            # Extraer los resultados
            total_archivos = resultados['total_archivos']
            total_carpetas = resultados['total_carpetas']
            archivos_por_carpeta = resultados['archivos_por_carpeta']
            archivos_por_extension = resultados['archivos_por_extension']
            lista_archivos = resultados['lista_archivos']
            archivos_placeholder = resultados['archivos_placeholder']
            archivos_similares = resultados.get('archivos_similares', defaultdict(list))

            # Mostrar resultados
            self.stdout.write(self.style.SUCCESS(f"\nResumen de conteo:"))
            self.stdout.write(f"- Total de carpetas: {total_carpetas}")
            self.stdout.write(f"- Total de archivos: {total_archivos}")
            if archivos_placeholder > 0:
                self.stdout.write(f"- Archivos placeholder ignorados: {archivos_placeholder}")
            
            # Mostrar archivos por carpeta
            self.stdout.write("\nArchivos por carpeta:")
            for carpeta, count in sorted(archivos_por_carpeta.items()):
                if carpeta == "":
                    carpeta_nombre = "[Raíz]"
                else:
                    carpeta_nombre = carpeta
                self.stdout.write(f"  {carpeta_nombre}: {count} archivos")
                
                # Si se solicitó detalle, mostrar los archivos de esta carpeta
                if show_detail and lista_archivos[carpeta]:
                    for archivo in sorted(lista_archivos[carpeta]):
                        self.stdout.write(f"    - {archivo}")
            
            # Mostrar archivos por extensión
            self.stdout.write("\nArchivos por extensión:")
            for ext, count in sorted(archivos_por_extension.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  {ext}: {count} archivos")
            
            # Mostrar archivos con nombres similares si se solicitó
            if find_duplicates and archivos_similares:
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write(self.style.SUCCESS("ARCHIVOS CON NOMBRES SIMILARES (BASADOS EN CLAVES DE PRODUCTO)"))
                self.stdout.write("=" * 50)
                
                for clave, archivos in sorted(archivos_similares.items(), key=lambda x: len(x[1]), reverse=True):
                    if len(archivos) > 1:  # Solo mostrar si hay más de un archivo con la misma clave
                        self.stdout.write(f"\nClave de producto: {clave} - {len(archivos)} archivos:")
                        for ruta_completa in sorted(archivos):
                            carpeta, archivo = os.path.split(ruta_completa)
                            if not carpeta:
                                carpeta = "[Raíz]"
                            self.stdout.write(f"  - {carpeta}/{archivo}")
                
                # Mostrar el total de claves con archivos similares
                claves_con_duplicados = sum(1 for archivos in archivos_similares.values() if len(archivos) > 1)
                self.stdout.write("\n" + "-" * 50)
                self.stdout.write(self.style.SUCCESS(f"Total de claves de producto con archivos similares: {claves_con_duplicados}"))
                self.stdout.write("-" * 50)
                
            # Mostrar el total general al final con un formato destacado
            total_suma = sum(archivos_por_carpeta.values())
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS(f"TOTAL DE ARCHIVOS EN EL BUCKET: {total_suma}"))
            self.stdout.write("=" * 50)
            
            # Verificar que los totales coincidan
            if total_suma != total_archivos:
                self.stdout.write(self.style.WARNING(
                    f"ADVERTENCIA: Hay una discrepancia en los conteos. "
                    f"Total calculado: {total_archivos}, Suma por carpetas: {total_suma}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al conectar con Supabase: {str(e)}"))
            logger.error(f"Error al conectar con Supabase: {str(e)}")

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
                logger.error(f"Error al listar contenido de {ruta_actual}: {str(e)}")
                break
                
        return todos_los_items

    def extraer_clave_producto(self, nombre_archivo):
        """Extrae la clave de producto del nombre del archivo usando expresiones regulares"""
        # Patrón para buscar claves de producto (letras seguidas de números)
        # Por ejemplo: GAA704, ABC123, etc.
        patron = re.compile(r'([A-Za-z]{2,3}\d{3,4})')
        coincidencia = patron.search(nombre_archivo)
        
        if coincidencia:
            return coincidencia.group(1).upper()  # Normalizar a mayúsculas
        return None

    def contar_archivos_recursivo(self, supabase, bucket_name, ruta_actual, recursive, all_files, show_detail, find_duplicates):
        # Inicializar contadores y estructuras de datos
        total_archivos = 0
        total_carpetas = 0
        archivos_por_carpeta = defaultdict(int)
        archivos_por_extension = defaultdict(int)
        lista_archivos = defaultdict(list)
        archivos_placeholder = 0
        archivos_similares = defaultdict(list)
        
        try:
            # Listar contenido de la carpeta actual con paginación
            self.stdout.write(f"Listando contenido de {ruta_actual or '[Raíz]'}...")
            contenido = self.listar_contenido_con_paginacion(supabase, bucket_name, ruta_actual)
            self.stdout.write(f"Total de elementos encontrados en {ruta_actual or '[Raíz]'}: {len(contenido)}")

            # Contar carpetas y archivos
            carpetas = []
            archivos = []
            
            for item in contenido:
                nombre_item = item["name"]
                es_carpeta = item.get("id") is None
                
                # Construir la ruta completa para el elemento actual
                if ruta_actual:
                    ruta_completa = f"{ruta_actual}/{nombre_item}"
                else:
                    ruta_completa = nombre_item
                
                if es_carpeta:
                    carpetas.append((nombre_item, ruta_completa))
                else:
                    archivos.append(nombre_item)
            
            # Actualizar contadores para esta carpeta
            total_carpetas += len(carpetas)
            
            # Procesar archivos de la carpeta actual
            archivos_validos = 0
            for archivo in archivos:
                # Contar o ignorar archivos placeholder
                if archivo == ".emptyFolderPlaceholder":
                    archivos_placeholder += 1
                    continue
                    
                total_archivos += 1
                archivos_validos += 1
                lista_archivos[ruta_actual].append(archivo)
                
                # Contar por extensión
                if '.' in archivo:
                    extension = archivo.rsplit('.', 1)[1].lower()
                    archivos_por_extension[f".{extension}"] += 1
                else:
                    archivos_por_extension["[sin extensión]"] += 1
                
                # Si se solicitó buscar archivos similares, extraer clave de producto
                if find_duplicates:
                    clave_producto = self.extraer_clave_producto(archivo)
                    if clave_producto:
                        # Guardar la ruta completa para facilitar la identificación
                        ruta_archivo = f"{ruta_actual}/{archivo}" if ruta_actual else archivo
                        archivos_similares[clave_producto].append(ruta_archivo)
            
            # Actualizar contador de archivos por carpeta (solo archivos válidos)
            archivos_por_carpeta[ruta_actual] = archivos_validos
            
            # Si es recursivo, procesar subcarpetas
            if recursive:
                for nombre_carpeta, ruta_carpeta in carpetas:
                    # Obtener resultados de la subcarpeta
                    resultados_subcarpeta = self.contar_archivos_recursivo(
                        supabase, bucket_name, ruta_carpeta, recursive, all_files, show_detail, find_duplicates
                    )
                    
                    # Acumular contadores
                    total_archivos += resultados_subcarpeta['total_archivos']
                    total_carpetas += resultados_subcarpeta['total_carpetas']
                    archivos_placeholder += resultados_subcarpeta['archivos_placeholder']
                    
                    # Acumular archivos por carpeta
                    for carpeta, count in resultados_subcarpeta['archivos_por_carpeta'].items():
                        archivos_por_carpeta[carpeta] = count
                    
                    # Acumular archivos por extensión
                    for ext, count in resultados_subcarpeta['archivos_por_extension'].items():
                        archivos_por_extension[ext] += count
                    
                    # Acumular lista de archivos
                    for carpeta, archivos in resultados_subcarpeta['lista_archivos'].items():
                        lista_archivos[carpeta].extend(archivos)
                    
                    # Acumular archivos similares
                    if find_duplicates and 'archivos_similares' in resultados_subcarpeta:
                        for clave, archivos in resultados_subcarpeta['archivos_similares'].items():
                            archivos_similares[clave].extend(archivos)
            
            # Retornar todos los contadores y estructuras de datos
            return {
                'total_archivos': total_archivos,
                'total_carpetas': total_carpetas,
                'archivos_por_carpeta': archivos_por_carpeta,
                'archivos_por_extension': archivos_por_extension,
                'lista_archivos': lista_archivos,
                'archivos_placeholder': archivos_placeholder,
                'archivos_similares': archivos_similares
            }
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al procesar carpeta {ruta_actual}: {str(e)}"))
            logger.error(f"Error al procesar carpeta {ruta_actual}: {str(e)}")
            
            # En caso de error, retornar contadores actuales
            return {
                'total_archivos': total_archivos,
                'total_carpetas': total_carpetas,
                'archivos_por_carpeta': archivos_por_carpeta,
                'archivos_por_extension': archivos_por_extension,
                'lista_archivos': lista_archivos,
                'archivos_placeholder': archivos_placeholder,
                'archivos_similares': archivos_similares
            }
