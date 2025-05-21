import requests
from typing import Dict, Any
from django.conf import settings
import json
from decimal import Decimal

# Clase para serializar Decimal a float
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class OdooService:
    def __init__(self, url=None):
        # Endpoint REST para crear órdenes
        self.order_endpoint = url or settings.ODOO_ENDPOINT
        self.login = settings.ODOO_LOGIN
        self.password = settings.ODOO_PASSWORD
        self.api_key = settings.ODOO_API_KEY
    
    def create_sales_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una orden de venta en Odoo usando el endpoint REST específico
        
        Args:
            order_data: Diccionario con los datos de la orden en formato Odoo
                
        Returns:
            Diccionario con la información de la orden creada
        """
        try:
            # Preparar el payload en el formato específico requerido por el endpoint
            payload = {
                "fields": ["name", "partner_id", "client_order_ref", "priority", "order_line"],
                "values": order_data
            }
            
            print("\n===== PAYLOAD ENVIADO A ODOO =====")
            print(json.dumps(payload, indent=4, cls=DecimalEncoder))
            print("====================================\n")
            
            # Convertir el payload a JSON usando el encoder personalizado
            payload_json = json.dumps(payload, cls=DecimalEncoder)
            
            # Preparar los headers con las credenciales
            headers = {
                'Content-Type': 'application/json',
                'login': self.login,
                'password': self.password,
                'api_key': self.api_key
            }
            
            # Realizar la petición POST al endpoint
            response = requests.post(
                self.order_endpoint, 
                data=payload_json,
                headers=headers
            )
            
            print("\n===== RESPUESTA DE ODOO =====")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            print("===============================\n")
            
            # Verificar si la petición fue exitosa
            response.raise_for_status()
            
            # Procesar la respuesta
            result = response.json()
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la petición HTTP: {str(e)}")
            raise Exception(f"Error al crear orden de venta en Odoo: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            raise Exception(f"Error inesperado al crear orden de venta en Odoo: {str(e)}")
