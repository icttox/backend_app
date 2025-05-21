"""
Utilidades para manejar la subida de archivos a Supabase Storage.
"""

import os
import requests
from datetime import datetime
from .supabase_config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME, get_public_url

def upload_file_to_supabase(file_path, object_name=None):
    """
    Sube un archivo a Supabase Storage.
    
    Args:
        file_path (str): Ruta local al archivo
        object_name (str, optional): Nombre del objeto en el bucket. 
                                   Si no se proporciona, se generará uno basado en el nombre del archivo.
    
    Returns:
        tuple: (URL pública si el archivo se subió correctamente, None si hubo un error),
               (None si se subió correctamente, mensaje de error si hubo un error)
    """
    if not os.path.exists(file_path):
        return None, f"El archivo {file_path} no existe"

    # Si no se proporciona un nombre de objeto, genera uno basado en la fecha y el nombre original
    if not object_name:
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        object_name = f"{timestamp}_{file_name}"

    # Prepara los headers para la solicitud
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/octet-stream'
    }

    # URL para la subida
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{object_name}"

    try:
        with open(file_path, 'rb') as f:
            response = requests.post(upload_url, headers=headers, data=f)
        
        if response.status_code == 200:
            return get_public_url(object_name), None
        else:
            return None, f"Error al subir el archivo: {response.text}"
    
    except Exception as e:
        return None, f"Error durante la subida: {str(e)}"

def delete_file_from_supabase(object_name):
    """
    Elimina un archivo de Supabase Storage.
    
    Args:
        object_name (str): Nombre del objeto en el bucket
    
    Returns:
        tuple: (True si se eliminó correctamente, False si hubo un error),
               (None si se eliminó correctamente, mensaje de error si hubo un error)
    """
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }

    delete_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{object_name}"

    try:
        response = requests.delete(delete_url, headers=headers)
        
        if response.status_code in [200, 204]:
            return True, None
        else:
            return False, f"Error al eliminar el archivo: {response.text}"
    
    except Exception as e:
        return False, f"Error durante la eliminación: {str(e)}"
