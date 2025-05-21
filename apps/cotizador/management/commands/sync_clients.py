from django.core.management.base import BaseCommand
from django.db import transaction
from apps.cotizador.models import Cliente
import requests
import logging
from datetime import datetime
import json
from apps.cotizador.cache.sync import sync_clients_to_supabase

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza los clientes desde la API de Odoo a la base de datos local'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user_id',
            type=int,
            default=1,
            help='ID del usuario para filtrar los clientes'
        )
        parser.add_argument(
            '--fecha_ini',
            type=str,
            default='2009-09-01',
            help='Fecha inicial para filtrar los clientes (formato: YYYY-MM-DD)'
        )
        parser.add_argument(
            '--fecha_fin',
            type=str,
            default='2025-09-04',
            help='Fecha final para filtrar los clientes (formato: YYYY-MM-DD)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='gebesa',
            help='Nombre para filtrar los clientes'
        )
        parser.add_argument(
            '--skip_django',
            action='store_true',
            help='Omitir la sincronización con Django y solo sincronizar con Supabase'
        )
        parser.add_argument(
            '--skip_supabase',
            action='store_true',
            help='Omitir la sincronización con Supabase'
        )

    def handle(self, *args, **options):
        start_time = datetime.now()
        logger.info(f"Iniciando sincronización de clientes: {start_time}")
        
        # Obtener los parámetros de la línea de comandos
        user_id = options['user_id']
        fecha_ini = options['fecha_ini']
        fecha_fin = options['fecha_fin']
        name = options['name']
        skip_django = options['skip_django']
        skip_supabase = options['skip_supabase']
        
        try:
            # Construir la URL con los parámetros
            api_url = f"https://api.ercules.mx/api/v1/common/res_partner"
            params = {
                'user_id': user_id,
                'fecha_ini': fecha_ini,
                'fecha_fin': fecha_fin,
                'name': name
            }
            
            # Realizar la petición a la API
            self.stdout.write(self.style.SUCCESS(f"Consultando API: {api_url}"))
            response = requests.get(api_url, params=params)
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Error al consultar la API: {response.status_code}"))
                logger.error(f"Error al consultar la API: {response.status_code}")
                return
            
            # Convertir la respuesta a JSON
            clients_data = response.json()
            
            if not clients_data:
                self.stdout.write(self.style.WARNING("No se encontraron clientes en la API"))
                logger.warning("No se encontraron clientes en la API")
                return
            
            self.stdout.write(self.style.SUCCESS(f"Se encontraron {len(clients_data)} clientes en la API"))
            
            # Sincronizar con Django si no se omitió
            if not skip_django:
                self.stdout.write(self.style.SUCCESS("Sincronizando con Django..."))
                try:
                    self._sync_clients_to_django(clients_data)
                    self.stdout.write(self.style.SUCCESS("Sincronización con Django completada."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error en la sincronización con Django: {str(e)}"))
                    logger.error(f"Error en la sincronización con Django: {str(e)}")
            
            # Sincronizar con Supabase si no se omitió
            if not skip_supabase:
                self.stdout.write(self.style.SUCCESS("Sincronizando con Supabase..."))
                try:
                    supabase_stats = sync_clients_to_supabase(clients_data)
                    self.stdout.write(self.style.SUCCESS(f"Sincronización con Supabase completada. Clientes sincronizados: {supabase_stats['successful']}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error en la sincronización con Supabase: {str(e)}"))
                    logger.error(f"Error en la sincronización con Supabase: {str(e)}")
            
            end_time = datetime.now()
            duration = end_time - start_time
            self.stdout.write(self.style.SUCCESS(f"Sincronización completada en {duration}"))
            logger.info(f"Sincronización completada en {duration}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error durante la sincronización: {str(e)}"))
            logger.error(f"Error durante la sincronización: {str(e)}")
    
    def _sync_clients_to_django(self, clients_data):
        """Sincroniza los clientes con la base de datos local de Django"""
        try:
            with transaction.atomic():
                # Contador para estadísticas
                created_count = 0
                updated_count = 0
                error_count = 0
                
                for client in clients_data:
                    try:
                        # Extraer los campos necesarios del cliente
                        partner_id = client.get('partner_id')
                        
                        if not partner_id:
                            logger.warning(f"Cliente sin partner_id: {client}")
                            error_count += 1
                            continue
                        
                        # Asegurarse de que partner_id sea un entero
                        try:
                            partner_id = int(partner_id)
                        except (ValueError, TypeError):
                            logger.warning(f"partner_id no es un entero válido: {partner_id}")
                            error_count += 1
                            continue
                        
                        name_partner = client.get('name_partner', '')
                        rfc = client.get('rfc', '')
                        
                        # Verificar si el cliente ya existe antes de usar update_or_create
                        try:
                            cliente = Cliente.objects.get(partner_id=partner_id)
                            # Actualizar campos
                            cliente.name_partner = name_partner
                            cliente.rfc = rfc
                            cliente.save()
                            updated_count += 1
                        except Cliente.DoesNotExist:
                            # Crear nuevo cliente
                            cliente = Cliente(
                                partner_id=partner_id,
                                name_partner=name_partner,
                                rfc=rfc
                            )
                            cliente.save()
                            created_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error al procesar cliente {client.get('partner_id')}: {str(e)}")
                        error_count += 1
                
                self.stdout.write(self.style.SUCCESS(f"Clientes creados: {created_count}"))
                self.stdout.write(self.style.SUCCESS(f"Clientes actualizados: {updated_count}"))
                self.stdout.write(self.style.SUCCESS(f"Errores: {error_count}"))
                logger.info(f"Clientes creados: {created_count}")
                logger.info(f"Clientes actualizados: {updated_count}")
                logger.info(f"Errores: {error_count}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error en la transacción: {str(e)}"))
            logger.error(f"Error en la transacción: {str(e)}")
            raise
