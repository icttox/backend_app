from django.core.management.base import BaseCommand
from supabase import create_client, Client
from apps.cotizador.cache.models import ProductsCache
import os
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Compara los archivos en la carpeta Prime de Supabase con los registros de ProductsCache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detail',
            action='store_true',
            dest='detail',
            default=False,
            help='Mostrar detalle completo de archivos y productos',
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='Prime',
            help='Nombre de la carpeta a comparar (por defecto: Prime)',
        )
        parser.add_argument(
            '--show-duplicates',
            action='store_true',
            dest='show_duplicates',
            default=False,
            help='Mostrar archivos que comparten la misma clave de producto',
        )
        parser.add_argument(
            '--min-files',
            type=int,
            default=2,
            help='Número mínimo de archivos para considerar como duplicados (por defecto: 2)',
        )

    def handle(self, *args, **options):
        SUPABASE_URL = "https://wlwxbdlmrcgjzmnjovbm.supabase.co"
        SUPABASE_KEY = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indsd3hiZGxtcmNnanptbmpvdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTM4MjI1MSwiZXhwIjoyMDU0OTU4MjUxfQ.QgMuPGN3I3WDv5G7nYK5DR23eiyBZfbf_tn2ZjxhCa8"
        )
        BUCKET_NAME = "imagenes-productos"
        show_detail = options['detail']
        folder_name = options['folder']
        show_duplicates = options['show_duplicates']
        min_files = options['min_files']

        # Contadores y estructuras de datos
        archivos_storage = []
        codigos_producto_storage = set()
        productos_cache = []
        codigos_producto_cache = set()
        # Diccionario para agrupar archivos por código de producto
        archivos_por_codigo = defaultdict(list)

        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.stdout.write(self.style.SUCCESS(f"Conexión exitosa a Supabase"))

            # 1. Obtener archivos de la carpeta especificada en Supabase Storage
            self.stdout.write(f"Obteniendo archivos de la carpeta '{folder_name}' en Supabase Storage...")
            ruta_carpeta = f"Imagenes/{folder_name}"
            archivos_storage = self.listar_contenido_con_paginacion(supabase, BUCKET_NAME, ruta_carpeta)
            
            # Extraer códigos de producto de los nombres de archivo
            for archivo in archivos_storage:
                nombre_archivo = archivo["name"]
                codigo_producto = self.extraer_clave_producto(nombre_archivo)
                if codigo_producto:
                    codigos_producto_storage.add(codigo_producto)
                    # Guardar el archivo en el diccionario agrupado por código
                    archivos_por_codigo[codigo_producto].append(nombre_archivo)

            # 2. Obtener productos de ProductsCache con line_name igual al nombre de la carpeta
            self.stdout.write(f"Obteniendo productos de ProductsCache con line_name='{folder_name}'...")
            productos_cache = list(ProductsCache.objects.filter(line_name__iexact=folder_name, active=True))
            
            # Extraer códigos de producto de ProductsCache
            for producto in productos_cache:
                codigo_producto = self.extraer_clave_producto(producto.reference_mask)
                if codigo_producto:
                    codigos_producto_cache.add(codigo_producto)

            # 3. Comparar resultados
            self.stdout.write(self.style.SUCCESS(f"\nResultados de la comparación:"))
            self.stdout.write(f"- Total de archivos en Storage (carpeta {folder_name}): {len(archivos_storage)}")
            self.stdout.write(f"- Total de códigos de producto únicos en Storage: {len(codigos_producto_storage)}")
            self.stdout.write(f"- Total de productos en ProductsCache (line_name={folder_name}): {len(productos_cache)}")
            self.stdout.write(f"- Total de códigos de producto únicos en tabla de ProductsCache: {len(codigos_producto_cache)}")
            
            # Calcular estadísticas de archivos duplicados
            archivos_unicos = len(codigos_producto_storage)
            archivos_totales = len(archivos_storage)
            archivos_duplicados = archivos_totales - archivos_unicos
            porcentaje_duplicados = (archivos_duplicados / archivos_totales * 100) if archivos_totales > 0 else 0
            
            # Mostrar resumen de imágenes únicas vs totales
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS(f"RESUMEN DE IMÁGENES ÚNICAS VS TOTALES"))
            self.stdout.write("=" * 50)
            self.stdout.write(f"\n- Total de archivos en Storage: {archivos_totales}")
            self.stdout.write(f"- Total de imágenes únicas (por código de producto): {archivos_unicos}")
            self.stdout.write(f"- Archivos duplicados o variantes: {archivos_duplicados}")
            self.stdout.write(f"- Porcentaje de duplicación: {porcentaje_duplicados:.2f}%")
            
            # Distribución de archivos por código de producto
            distribucion = defaultdict(int)
            for codigo, archivos in archivos_por_codigo.items():
                distribucion[len(archivos)] += 1
            
            self.stdout.write("\nDistribución de archivos por código de producto:")
            for num_archivos, cantidad in sorted(distribucion.items()):
                self.stdout.write(f"  - Códigos con {num_archivos} archivo{'s' if num_archivos > 1 else ''}: {cantidad}")

            # Mostrar archivos que comparten la misma clave única
            if show_duplicates:
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write(self.style.SUCCESS(f"ARCHIVOS QUE COMPARTEN LA MISMA CLAVE DE PRODUCTO"))
                self.stdout.write("=" * 50)
                
                # Filtrar códigos con múltiples archivos
                codigos_con_multiples_archivos = {codigo: archivos for codigo, archivos in archivos_por_codigo.items() 
                                                if len(archivos) >= min_files}
                
                if codigos_con_multiples_archivos:
                    self.stdout.write(f"\nSe encontraron {len(codigos_con_multiples_archivos)} códigos de producto con {min_files} o más archivos:")
                    
                    # Ordenar por código de producto
                    for codigo, archivos in sorted(codigos_con_multiples_archivos.items()):
                        self.stdout.write(f"\nCódigo de producto: {codigo} - {len(archivos)} archivos:")
                        for archivo in sorted(archivos):
                            self.stdout.write(f"  - {archivo}")
                else:
                    self.stdout.write(f"\nNo se encontraron códigos de producto con {min_files} o más archivos.")

            # 4. Encontrar diferencias
            codigos_solo_storage = codigos_producto_storage - codigos_producto_cache
            codigos_solo_cache = codigos_producto_cache - codigos_producto_storage
            codigos_en_ambos = codigos_producto_storage.intersection(codigos_producto_cache)

            # 5. Mostrar diferencias
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS(f"ANÁLISIS DE DIFERENCIAS"))
            self.stdout.write("=" * 50)
            
            self.stdout.write(f"\nCódigos presentes en ambos sistemas: {len(codigos_en_ambos)}")
            if show_detail and codigos_en_ambos:
                self.stdout.write("Códigos en ambos:")
                for codigo in sorted(codigos_en_ambos):
                    self.stdout.write(f"  - {codigo}")

            self.stdout.write(f"\nCódigos solo en Storage (sin registro en ProductsCache): {len(codigos_solo_storage)}")
            if codigos_solo_storage:
                for codigo in sorted(codigos_solo_storage):
                    archivos_relacionados = [a["name"] for a in archivos_storage 
                                          if self.extraer_clave_producto(a["name"]) == codigo]
                    self.stdout.write(f"  - {codigo}: {len(archivos_relacionados)} archivos")
                    if show_detail:
                        for archivo in sorted(archivos_relacionados):
                            self.stdout.write(f"      {archivo}")

            self.stdout.write(f"\nCódigos solo en ProductsCache (sin imágenes en Storage): {len(codigos_solo_cache)}")
            if codigos_solo_cache:
                for codigo in sorted(codigos_solo_cache):
                    productos_relacionados = [p for p in productos_cache 
                                           if self.extraer_clave_producto(p.reference_mask) == codigo]
                    self.stdout.write(f"  - {codigo}: {len(productos_relacionados)} productos")
                    if show_detail:
                        for producto in sorted(productos_relacionados, key=lambda p: p.reference_mask):
                            self.stdout.write(f"      {producto.reference_mask} - {producto.name}")

            # 6. Verificar productos con imágenes asignadas pero que no existen en Storage
            productos_con_url = [p for p in productos_cache if p.image_url and 
                               self.extraer_clave_producto(p.reference_mask) in codigos_solo_cache]
            
            if productos_con_url:
                self.stdout.write("\n" + "-" * 50)
                self.stdout.write(self.style.WARNING(
                    f"ADVERTENCIA: {len(productos_con_url)} productos tienen URL de imagen asignada "
                    f"pero no se encontraron imágenes correspondientes en Storage"
                ))
                self.stdout.write("-" * 50)
                
                if show_detail:
                    for producto in productos_con_url:
                        self.stdout.write(f"  - {producto.reference_mask} - {producto.name}")
                        self.stdout.write(f"    URL: {producto.image_url}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error: {str(e)}")

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
                    
                # Filtrar solo archivos (no carpetas)
                archivos = [item for item in contenido if item.get("id") is not None]
                todos_los_items.extend(archivos)
                
                # Si recibimos menos elementos que el límite, significa que hemos terminado
                if len(contenido) < limit:
                    break
                    
                # Incrementar el offset para la siguiente solicitud
                offset += limit
                
                # Informar del progreso
                self.stdout.write(f"  Obtenidos {len(todos_los_items)} archivos de {ruta_actual or '[Raíz]'}...")
                
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
