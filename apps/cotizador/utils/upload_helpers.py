"""
Utilidades para manejar la subida de imágenes de productos a Supabase Storage.
"""

import os
import uuid
import tempfile
import re
from django.conf import settings
from datetime import datetime
import requests
import json
from supabase import create_client, Client

def upload_image_to_supabase(image_file, line_name, reference_mask):
    """
    Sube una imagen a Supabase Storage en una carpeta organizada por línea de producto.
    
    Args:
        image_file: Archivo de imagen (InMemoryUploadedFile)
        line_name: Nombre de la línea del producto
        reference_mask: Identificador único del producto
    
    Returns:
        tuple: (URL pública si la imagen se subió correctamente, None si hubo un error),
               (None si se subió correctamente, mensaje de error si hubo un error)
    """
    # Depuración: Imprimir todas las variables de entorno relacionadas con Supabase
    print("\nDEBUG: VERIFICACIÓN DE VARIABLES DE ENTORNO SUPABASE:")
    print(f"DEBUG: SUPABASE_URL = {getattr(settings, 'SUPABASE_URL', 'NO DEFINIDO')}")
    print(f"DEBUG: SUPABASE_KEY = {getattr(settings, 'SUPABASE_KEY', 'NO DEFINIDO')[:10]}... (si existe)")
    print(f"DEBUG: SUPABASE_SERVICE_KEY = {getattr(settings, 'SUPABASE_SERVICE_KEY', 'NO DEFINIDO')[:10]}... (si existe)")
    print(f"DEBUG: SUPABASE_BUCKET_NAME = {getattr(settings, 'SUPABASE_BUCKET_NAME', 'NO DEFINIDO')}")
    print(f"DEBUG: SECRET_KEY = {getattr(settings, 'SECRET_KEY', 'NO DEFINIDO')[:10]}... (si existe)")
    print("\n")
    
    # Normalizar el nombre de la línea para usarlo como carpeta
    # Extraer solo la parte principal antes de paréntesis o caracteres especiales
    if line_name:
        # Eliminar espacios al inicio y final
        clean_line_name = line_name.strip()
        
        # Extraer la parte antes del primer paréntesis, guion o cualquier otro separador común
        match = re.match(r'^([^(|\-|–|,]+)', clean_line_name)
        if match:
            folder_name = match.group(1).strip()
        else:
            folder_name = clean_line_name
    else:
        folder_name = "otros"
    
    # Obtener la extensión del archivo
    file_extension = os.path.splitext(image_file.name)[1].lower()
    
    # Construir la ruta del objeto en Supabase Storage
    # Formato: Imagenes/[nombre_linea]/[reference_mask].[extension]
    storage_path = f"Imagenes/{folder_name}/{reference_mask}{file_extension}"
    
    # Guardar temporalmente el archivo
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        for chunk in image_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        # IMPORTANTE: Para operaciones de escritura en Storage, SIEMPRE usar la clave de servicio
        # La clave de servicio (service_role) ignora las políticas RLS
        print(f"DEBUG: SUPABASE_URL = {settings.SUPABASE_URL}")
        
        # Usar la clave de servicio preferentemente, o SECRET_KEY como fallback
        service_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
        if not service_key:
            print("INFO: SUPABASE_SERVICE_KEY no está definido en settings, usando SECRET_KEY como fallback")
            # Usar SECRET_KEY como fallback (que parece contener la clave de servicio en tu caso)
            service_key = getattr(settings, 'SECRET_KEY', None)
        
        print(f"DEBUG: Longitud de service_key = {len(service_key) if service_key else 0}")
        if service_key:
            print(f"DEBUG: Primeros 10 caracteres de service_key = {service_key[:10]}...")
            
        print(f"DEBUG: Longitud de service_key = {len(service_key)}")
        print(f"DEBUG: Primeros 10 caracteres de service_key = {service_key[:10]}...")
        
        # Nombre del bucket en Supabase Storage
        bucket_name = getattr(settings, 'SUPABASE_BUCKET_NAME', 'imagenes-productos')
        print(f"DEBUG: Bucket name = {bucket_name}")
        
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
            
            # URL para subir archivos a Supabase Storage
            upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
            
            # Cabeceras de la solicitud con el token apropiado
            headers = {
                "Authorization": f"Bearer {service_key}",
                "Content-Type": image_file.content_type,
                "x-upsert": "true"  # Para sobrescribir si ya existe
            }
            
            # Imprimir información de la solicitud para depuración
            print(f"DEBUG: URL de carga: {upload_url}")
            print(f"DEBUG: Tamaño del archivo: {len(file_content)} bytes")
            
            # Realizar la solicitud POST
            try:
                print(f"DEBUG: Enviando solicitud POST a {upload_url}")
                print(f"DEBUG: Headers: Authorization=Bearer {service_key[:10]}..., Content-Type={image_file.content_type}")
                response = requests.post(
                    upload_url,
                    headers=headers,
                    data=file_content
                )
                print(f"DEBUG: Respuesta recibida con status code: {response.status_code}")
                print(f"DEBUG: Respuesta completa: {response.text}")
            except Exception as e:
                print(f"DEBUG: Error al realizar la solicitud: {str(e)}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                raise
            
            # Verificar si la solicitud fue exitosa
            if response.status_code not in (200, 201):
                error_msg = f"Error en la API de Supabase: Status {response.status_code}\nRespuesta: {response.text}"
                print(f"DEBUG: {error_msg}")
                raise Exception(error_msg)
        
        # Eliminar el archivo temporal
        os.unlink(temp_file_path)
        
        # Inicializar el cliente de Supabase solo para obtener la URL pública
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY  # Aquí podemos usar la clave regular para solo lectura
        )
        
        # Construir la URL pública
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        
        return public_url, None
    
    except Exception as e:
        # Asegurarse de eliminar el archivo temporal en caso de error
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return None, f"Error durante la subida: {str(e)}"


def upload_kit_image_to_supabase(image_file, kit_uuid):
    """
    Sube una imagen de un kit a Supabase Storage.
    
    Args:
        image_file: Archivo de imagen (InMemoryUploadedFile)
        kit_uuid: UUID del kit
    
    Returns:
        tuple: (URL pública si la imagen se subió correctamente, None si hubo un error),
               (None si se subió correctamente, mensaje de error si hubo un error),
               (Ruta de almacenamiento en Supabase si se subió correctamente, None si hubo un error)
    """
    # Obtener la extensión del archivo
    file_extension = os.path.splitext(image_file.name)[1].lower()
    
    # Construir la ruta del objeto en Supabase Storage
    # Formato: Imagenes/kits/[kit_uuid].[extension]
    storage_path = f"Imagenes/kits/{kit_uuid}{file_extension}"
    
    # Guardar temporalmente el archivo
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        for chunk in image_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        # IMPORTANTE: Para operaciones de escritura en Storage, SIEMPRE usar la clave de servicio
        # La clave de servicio (service_role) ignora las políticas RLS
        # Usar la clave de servicio preferentemente, o SECRET_KEY como fallback
        service_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
        if not service_key:
            print("INFO: SUPABASE_SERVICE_KEY no está definido en settings, usando SECRET_KEY como fallback")
            # Usar SECRET_KEY como fallback (que parece contener la clave de servicio en tu caso)
            service_key = getattr(settings, 'SECRET_KEY', None)
        
        print(f"DEBUG: Longitud de service_key = {len(service_key) if service_key else 0}")
        if service_key:
            print(f"DEBUG: Primeros 10 caracteres de service_key = {service_key[:10]}...")
        
        # Nombre del bucket en Supabase Storage
        bucket_name = 'imagenes-kits'
        
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
            
            # URL para subir archivos a Supabase Storage
            upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
            
            # Cabeceras de la solicitud con token de servicio
            headers = {
                "Authorization": f"Bearer {service_key}",
                "Content-Type": image_file.content_type,
                "x-upsert": "true"  # Para sobrescribir si ya existe
            }
            
            # Imprimir información de la solicitud para depuración
            print(f"DEBUG: URL de carga: {upload_url}")
            print(f"DEBUG: Tamaño del archivo: {len(file_content)} bytes")
            
            # Realizar la solicitud POST
            try:
                print(f"DEBUG: Enviando solicitud POST a {upload_url}")
                print(f"DEBUG: Headers: Authorization=Bearer {service_key[:10]}..., Content-Type={image_file.content_type}")
                response = requests.post(
                    upload_url,
                    headers=headers,
                    data=file_content
                )
                print(f"DEBUG: Respuesta recibida con status code: {response.status_code}")
                print(f"DEBUG: Respuesta completa: {response.text}")
            except Exception as e:
                print(f"DEBUG: Error al realizar la solicitud: {str(e)}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                raise
            
            # Verificar si la solicitud fue exitosa
            if response.status_code not in (200, 201):
                error_msg = f"Error en la API de Supabase: Status {response.status_code}\nRespuesta: {response.text}"
                print(f"DEBUG: {error_msg}")
                raise Exception(error_msg)
        
        # Eliminar el archivo temporal
        os.unlink(temp_file_path)
        
        # Inicializar el cliente de Supabase solo para obtener la URL pública
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY  # Aquí podemos usar la clave regular para solo lectura
        )
        
        # Construir la URL pública
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        
        return public_url, None, storage_path
    
    except Exception as e:
        # Asegurarse de eliminar el archivo temporal en caso de error
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return None, f"Error durante la subida: {str(e)}", None


def upload_kit_image_without_uuid(image_file):
    """
    Sube una imagen de un kit a Supabase Storage sin requerir UUID.
    Genera un nombre único basado en timestamp y hash.
    
    Args:
        image_file: Archivo de imagen (InMemoryUploadedFile)
    
    Returns:
        tuple: (URL pública si la imagen se subió correctamente, None si hubo un error),
               (None si se subió correctamente, mensaje de error si hubo un error),
               (Ruta de almacenamiento en Supabase si se subió correctamente, None si hubo un error)
    """
    try:
        print("DEBUG: Iniciando upload_kit_image_without_uuid")
        # Obtener la extensión del archivo
        file_extension = os.path.splitext(image_file.name)[1].lower()
        print(f"DEBUG: Extensión del archivo: {file_extension}")
        
        # Generar un nombre único basado en timestamp y hash del contenido
        import time
        import hashlib
        timestamp = int(time.time() * 1000)
        print(f"DEBUG: Timestamp: {timestamp}")
        
        # Crear un hash del nombre del archivo y los primeros bytes para mayor unicidad
        hasher = hashlib.md5()
        print(f"DEBUG: Tipo de image_file.name: {type(image_file.name)}")
        hasher.update(image_file.name.encode())
        
        # Leer los primeros bytes del archivo para el hash sin consumir todo el archivo
        image_file.seek(0)
        print("DEBUG: Leyendo primeros bytes del archivo")
        content_sample = image_file.read(1024)  # Leer solo los primeros 1024 bytes
        print(f"DEBUG: Tipo de content_sample: {type(content_sample)}")
        image_file.seek(0)  # Volver al inicio del archivo
        
        # Asegurarse de que content_sample sea bytes antes de pasarlo a hasher.update
        if isinstance(content_sample, bytes):
            print("DEBUG: content_sample es bytes")
            hasher.update(content_sample)
        elif isinstance(content_sample, str):
            print("DEBUG: content_sample es string")
            hasher.update(content_sample.encode())
        elif content_sample is not None:
            print(f"DEBUG: content_sample es otro tipo: {type(content_sample)}")
            # Convertir a string y luego a bytes
            str_content = str(content_sample)
            print(f"DEBUG: str_content: {str_content[:50]}... (truncado)")
            hasher.update(str_content.encode())
        else:
            print("DEBUG: content_sample es None")
        
        file_hash = hasher.hexdigest()[:10]  # Usar solo los primeros 10 caracteres del hash
        print(f"DEBUG: Hash generado: {file_hash}")
        
        # Construir un nombre de archivo único
        unique_filename = f"kit_{timestamp}_{file_hash}{file_extension}"
        print(f"DEBUG: Nombre de archivo único: {unique_filename}")
        
        # Construir la ruta del objeto en Supabase Storage
        # Formato: Imagenes/kits/[unique_filename]
        storage_path = f"Imagenes/kits/{unique_filename}"
        print(f"DEBUG: Ruta de almacenamiento: {storage_path}")
        
        # Guardar temporalmente el archivo
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        print(f"DEBUG: Archivo temporal creado en: {temp_file_path}")
        
        # IMPORTANTE: Para operaciones de escritura en Storage, SIEMPRE usar la clave de servicio
        # La clave de servicio (service_role) ignora las políticas RLS
        # Usar la clave de servicio preferentemente, o SECRET_KEY como fallback
        service_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
        if not service_key:
            print("INFO: SUPABASE_SERVICE_KEY no está definido en settings, usando SECRET_KEY como fallback")
            # Usar SECRET_KEY como fallback (que parece contener la clave de servicio en tu caso)
            service_key = getattr(settings, 'SECRET_KEY', None)
        
        print(f"DEBUG: Longitud de service_key = {len(service_key) if service_key else 0}")
        if service_key:
            print(f"DEBUG: Primeros 10 caracteres de service_key = {service_key[:10]}...")
        
        # Nombre del bucket en Supabase Storage
        bucket_name = 'imagenes-kits'
        print(f"DEBUG: Usando bucket: {bucket_name}")
        
        # Subir el archivo a Supabase Storage
        print("DEBUG: Abriendo archivo para subir")
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
            print(f"DEBUG: Tamaño del archivo: {len(file_content)} bytes")
            print("DEBUG: Subiendo archivo a Supabase")
            
            # URL para subir archivos a Supabase Storage
            upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
            
            # Cabeceras de la solicitud con token de servicio
            headers = {
                "Authorization": f"Bearer {service_key}",
                "Content-Type": image_file.content_type,
                "x-upsert": "true"  # Para sobrescribir si ya existe
            }
            
            # Imprimir información de la solicitud para depuración
            print(f"DEBUG: URL de carga: {upload_url}")
            print(f"DEBUG: Tamaño del archivo: {len(file_content)} bytes")
            
            # Realizar la solicitud POST
            try:
                print(f"DEBUG: Enviando solicitud POST a {upload_url}")
                print(f"DEBUG: Headers: Authorization=Bearer {service_key[:10]}..., Content-Type={image_file.content_type}")
                response = requests.post(
                    upload_url,
                    headers=headers,
                    data=file_content
                )
                print(f"DEBUG: Respuesta recibida con status code: {response.status_code}")
                print(f"DEBUG: Respuesta completa: {response.text}")
            except Exception as e:
                print(f"DEBUG: Error al realizar la solicitud: {str(e)}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                raise
            
            # Verificar si la solicitud fue exitosa
            if response.status_code not in (200, 201):
                error_msg = f"Error en la API de Supabase: Status {response.status_code}\nRespuesta: {response.text}"
                print(f"DEBUG: {error_msg}")
                raise Exception(error_msg)
        
        # Construir la URL pública
        print("DEBUG: Obteniendo URL pública")
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY  # Aquí podemos usar la clave regular para solo lectura
        )
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        print(f"DEBUG: URL pública: {public_url}")
        
        return public_url, None, storage_path
    
    except Exception as e:
        import traceback
        print(f"DEBUG: Error en upload_kit_image_without_uuid: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        # Asegurarse de eliminar el archivo temporal en caso de error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return None, str(e), None
    
    finally:
        # Eliminar el archivo temporal
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            print("DEBUG: Eliminando archivo temporal")
            os.unlink(temp_file_path)
