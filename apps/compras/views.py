import json
import requests
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, F, Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.conf import settings

import logging # Ensure logging is imported
logger = logging.getLogger(__name__) # Define logger for this module

import requests
import json
from datetime import datetime, timedelta
from .services import OdooService, OdooAuthError, OdooApiError # Import custom exceptions
from .serializers import (
    CategoriaSerializer,
    UserComprasSerializer,
    AlmacenSerializer,
    PropuestaCompraListSerializer,
    PropuestaCompraDetailSerializer,
    PropuestaCompraCreateSerializer,
    PropuestaCompraUpdateSerializer,
    ItemPropuestaCompraSerializer,
    ItemPropuestaCompraCreateSerializer
)
from apps.accounts.models import User, UserProfile
from .models import Categoria, PropuestaCompra, ItemPropuestaCompra
from rest_framework.views import APIView
from django.http import Http404
from rest_framework.exceptions import ValidationError
from apps.cotizador.pagination import CustomPageNumberPagination

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar categorías de productos
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtra las categorías según parámetros
        """
        queryset = Categoria.objects.all()
            
        # Filtrar por categoría_id si se especifica
        categoria_id = self.request.query_params.get('categoria_id', None)
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        # Buscar por nombre
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
            
        # Solo mostrar activos por defecto a menos que se indique lo contrario
        mostrar_inactivos = self.request.query_params.get('mostrar_inactivos', 'false').lower() == 'true'
        if not mostrar_inactivos:
            queryset = queryset.filter(activo=True)
            
        return queryset



class UserComprasViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para gestionar la información de compras de los usuarios
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserComprasSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserProfile.objects.all()
        
        # Filtrar por usuario si se especifica
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrar por nombre de comprador si se especifica
        nombre_comprador = self.request.query_params.get('nombre_comprador', None)
        if nombre_comprador:
            queryset = queryset.filter(nombre_comprador=nombre_comprador)
        
        # Filtrar por categoría asignada
        categoria_id = self.request.query_params.get('categoria_id', None)
        if categoria_id:
            queryset = queryset.filter(categorias_compras_asignadas__categoria_id=categoria_id)
            
        return queryset
        
    @action(detail=False, methods=['GET'])
    def mis_categorias(self, request):
        """
        Devuelve las categorías de compras asignadas al usuario autenticado
        """
        usuario = request.user
        try:
            profile = usuario.profile
            categorias = profile.categorias_compras_asignadas.filter(activo=True)
            serializer = CategoriaSerializer(categorias, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": f"Error al obtener las categorías: {str(e)}"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['GET'])
    def mi_perfil(self, request):
        """
        Devuelve el perfil de compras del usuario autenticado
        """
        usuario = request.user
        try:
            profile = usuario.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": f"Error al obtener el perfil: {str(e)}"},
                status=status.HTTP_404_NOT_FOUND
            )

class AlmacenViewSet(viewsets.ViewSet):
    """
    API endpoint para consultar almacenes directamente desde la API externa
    No se almacenan datos localmente, todo se consulta en tiempo real
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        Obtiene la lista de almacenes directamente desde la API externa
        """
        # URL de la API externa para obtener almacenes
        api_url = 'https://api2.ercules.mx/api/v1/common/location_classifications'
        
        try:
            # Parámetros para la consulta
            params = {
                'user_id': 2,  # ID del usuario para la API externa
                'classification': 0,
                'names': 0
            }
            
            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error en la API externa: {response.status_code}',
                    'detail': response.text
                }, status=response.status_code)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al consultar la API externa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """
        Obtiene los detalles de un almacén específico directamente desde la API externa
        """
        # URL de la API externa para obtener almacenes
        api_url = 'https://api2.ercules.mx/api/v1/common/location_classifications'
        
        try:
            # Parámetros para la consulta
            params = {
                'user_id': 2,  # ID del usuario para la API externa
                'classification': 0,
                'names': 0
            }
            
            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                # Buscar el almacén específico por su ID
                almacenes_data = response.json()
                for item in almacenes_data.get('data', []):
                    if str(item.get('id')) == str(pk):
                        return Response(item)
                        
                # Si no se encuentra el almacén
                return Response({
                    'status': 'error',
                    'message': f'Almacén con ID {pk} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error en la API externa: {response.status_code}',
                    'detail': response.text
                }, status=response.status_code)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al consultar la API externa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=False, methods=['GET'])
    def test_connection(self, request):
        """
        Verifica la conectividad con la API externa de almacenes
        """
        # URL de la API externa para obtener almacenes
        api_url = 'https://api2.ercules.mx/api/v1/common/location_classifications'
        
        try:
            # Parámetros para la consulta
            params = {
                'user_id': 2,  # ID del usuario para la API externa
                'classification': 0,
                'names': 0
            }
            
            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                return Response({
                    'status': 'success',
                    'message': 'Conectividad con la API externa verificada correctamente',
                    'total_almacenes': len(response.json().get('data', []))
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error en la API externa: {response.status_code}',
                    'detail': response.text
                }, status=response.status_code)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al sincronizar almacenes: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProveedorViewSet(viewsets.ViewSet):
    """
    API endpoint para consultar proveedores directamente desde la API externa
    No se almacenan datos localmente, todo se consulta en tiempo real
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Obtiene la lista de proveedores directamente desde la API externa
        """
        # URL de la API externa para obtener proveedores
        api_url = 'https://api2.ercules.mx/api/v1/common/res_partner'

        # Obtener parámetros de la consulta, con valores por defecto razonables
        fecha_ini = request.query_params.get('fecha_ini', '2015-01-01')
        fecha_fin = request.query_params.get('fecha_fin', timezone.now().strftime('%Y-%m-%d'))
        name = request.query_params.get('name', '0') # Asumiendo '0' como valor por defecto si no se especifica nombre
        # El tipo 'supplier' parece fijo según el ejemplo
        proveedor_type = 'supplier'
        # El user_id parece fijo a 2 según el ejemplo
        user_id_externo = 2

        try:
            # Parámetros para la consulta a la API externa
            params = {
                'user_id': user_id_externo,
                'fecha_ini': fecha_ini,
                'fecha_fin': fecha_fin,
                'name': name,
                'type': proveedor_type
            }

            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)

            if response.status_code == 200:
                return Response(response.json())
            else:
                # Loguear el error para depuración interna podría ser útil aquí
                # logger.error(f"Error en API externa de proveedores: {response.status_code} - {response.text}")
                return Response({
                    'status': 'error',
                    'message': f'Error al consultar la API externa de proveedores: {response.status_code}',
                    'detail': response.text # Considerar si exponer el detail externo es seguro
                }, status=response.status_code)
        except requests.exceptions.RequestException as e:
            # Loguear el error de conexión
            # logger.error(f"Error de conexión al consultar API externa de proveedores: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Error de conexión al consultar la API externa: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE) # 503 podría ser más apropiado que 500
        except Exception as e:
            # Loguear error inesperado
            # logger.error(f"Error inesperado al consultar API externa de proveedores: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Error inesperado al consultar la API externa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoriaProductoViewSet(APIView):
    """
    API para obtener categorías de productos desde la API externa
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Obtiene la lista de categorías de productos desde la API externa
        """
        # URL de la API externa para obtener categorías de productos
        api_url = 'https://api2.ercules.mx/api/v1/common/product_classifications'
        
        try:
            # Parámetros para la consulta
            params = {
                'user_id': 2,  # ID del usuario para la API externa
                'classification': 0,
                'names': 0
            }
            
            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                categorias_data = response.json()
                
                # Si el comprador actual tiene restricciones de categorías, filtrar los resultados
                usuario = request.user
                try:
                    # Obtener el perfil del usuario
                    profile = usuario.profile
                    
                    # Verificar si el usuario tiene el área de compras
                    if profile.area == 'Compras':
                        # Obtener las categorías asignadas al usuario
                        categorias_permitidas = profile.categorias_compras_asignadas.filter(
                            activo=True
                        ).values_list('categoria_id', flat=True)
                        
                        # Si hay categorías permitidas, filtrar los resultados
                        if categorias_permitidas:
                            data_filtrada = [
                                item for item in categorias_data.get('data', [])
                                if str(item.get('id')) in [str(cat_id) for cat_id in categorias_permitidas]
                            ]
                            categorias_data['data'] = data_filtrada
                            categorias_data['total_count'] = len(data_filtrada)
                    
                    return Response(categorias_data)
                except Exception as e:
                    # Si hay algún error o el usuario no tiene perfil, devolver todas las categorías
                    # (esto podría restringirse según los requisitos)
                    return Response({
                        'status': 'warning',
                        'message': f'No se pudieron filtrar las categorías por permisos: {str(e)}',
                        'data': categorias_data['data'],
                        'total_count': categorias_data.get('total_count', 0)
                    })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error en la API externa: {response.status_code}',
                    'detail': response.text
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener categorías de productos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PronosticoExistenciasAPIView(APIView):
    """
    API para obtener el pronóstico de existencias desde la API externa
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Obtiene los datos del pronóstico de existencias para almacenes y categorías especificadas
        """
        # Obtener parámetros de la solicitud
        warehouse_ids = request.query_params.get('warehouse_ids', '0')  # Valor por defecto '0'
        categ_ids = request.query_params.get('categ_ids')
        group_ids = request.query_params.get('group_ids', '0')  # Valor por defecto '0'
        line_ids = request.query_params.get('line_ids', '0')    # Valor por defecto '0'
        products = request.query_params.get('products', '0')    # Valor por defecto '0'
        codes = request.query_params.get('codes', '0')          # Valor por defecto '0'
        order = request.query_params.get('order', 'consumption')
        limit = request.query_params.get('limit', '100')
        
        # Validar parámetros requeridos
        if not categ_ids:
            return Response({
                'status': 'error',
                'message': 'Se requiere el parámetro categ_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # URL de la API externa para pronóstico de existencias
        api_url = 'https://api2.ercules.mx/api/v1/stock/stock_forecasting'
        
        try:
            # Parámetros para la consulta
            params = {
                'user_id': 2,  # ID del usuario para la API externa
                'warehouse_ids': warehouse_ids,
                'categ_ids': categ_ids,
                'group_ids': group_ids,
                'line_ids': line_ids,
                'products': products,
                'codes': codes,
                'order': order,
                'limit': limit
            }
            
            # Realizar la solicitud a la API externa
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                pronostico_data = response.json()
                
                return Response(pronostico_data)
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error en la API externa: {response.status_code}',
                    'detail': response.text
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener pronóstico de existencias: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropuestaCompraViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar propuestas de compra
    """
    queryset = PropuestaCompra.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'mis_propuestas': 
            return PropuestaCompraListSerializer
        elif self.action == 'create':
            return PropuestaCompraCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return PropuestaCompraUpdateSerializer
        return PropuestaCompraDetailSerializer
    
    def get_queryset(self):
        queryset = PropuestaCompra.objects.all()
        
        # Filtrar por estado si se especifica
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtrar por comprador si se especifica
        comprador_id = self.request.query_params.get('comprador_id', None)
        if comprador_id:
            queryset = queryset.filter(comprador_id=comprador_id)
            
        # Ordenar por fecha de creación (más recientes primero)
        queryset = queryset.order_by('-fecha_creacion')
        
        return queryset
    
    @action(detail=False, methods=['GET'])
    def mis_propuestas(self, request):
        """
        Devuelve las propuestas de compra del comprador autenticado
        """
        usuario = request.user
        queryset = PropuestaCompra.objects.filter(comprador=usuario)
        
        # Filtrar por estado si se especifica
        estado = request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Ordenar por fecha de creación (más recientes primero)
        queryset = queryset.order_by('-fecha_creacion')
        
        # Aplicar paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True) # Use get_serializer for context
            return self.get_paginated_response(serializer.data)

        # Si no hay paginación (o no está configurada), devolver la lista completa
        serializer = self.get_serializer(queryset, many=True) # Use get_serializer for context
        return Response(serializer.data)
    
    # Renamed from 'enviar'
    @action(detail=True, methods=['POST'], url_path='solicitar-aprobacion')
    def solicitar_aprobacion(self, request, pk=None):
        """Marca una propuesta como pendiente de aprobación por el gerente."""
        propuesta = self.get_object()
        
        # Validar que la propuesta pertenezca al usuario que la envía (o es admin)
        if propuesta.comprador != request.user and not request.user.is_staff:
             return Response(
                 {'error': 'No tiene permiso para solicitar aprobación para esta propuesta.'},
                 status=status.HTTP_403_FORBIDDEN
             )
             
        # Verificar que haya al menos un item en la propuesta
        if not propuesta.items.exists(): 
            return Response(
                {"detail": "No se puede solicitar aprobación para una propuesta sin items"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar estado usando el método del modelo
        if propuesta.solicitar_aprobacion():
             serializer = self.get_serializer(propuesta) # Devolver estado actualizado
             return Response(serializer.data)
        else:
             return Response(
                 {'error': f'La propuesta ya se encuentra en estado {propuesta.get_estado_display()} y no puede ser enviada a aprobación.'},
                 status=status.HTTP_400_BAD_REQUEST
             )

    @action(detail=True, methods=['POST'])
    def aprobar(self, request, pk=None):
        """Aprueba una propuesta que está pendiente de aprobación."""
        propuesta = self.get_object()
        # TODO: Add permission check - e.g., only managers or staff can approve
        # if not request.user.is_staff: # Example check
        #     return Response({'error': 'No tiene permiso para aprobar propuestas.'}, status=status.HTTP_403_FORBIDDEN)
        
        comentarios = request.data.get('comentarios', None) # Obtener comentarios del request
            
        if propuesta.aprobar(request.user, comentarios=comentarios): # Pass user and comments
            serializer = self.get_serializer(propuesta)
            return Response(serializer.data)
        else:
            return Response(
                {'error': f'La propuesta no está en estado "Pendiente Aprobación" y no puede ser aprobada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def rechazar(self, request, pk=None):
        """Rechaza una propuesta que está pendiente de aprobación."""
        propuesta = self.get_object()
        comentarios = request.data.get('comentarios', None) # Opcional: obtener comentarios del request
        # TODO: Add permission check - e.g., only managers or staff can reject
        # if not request.user.is_staff:
        #     return Response({'error': 'No tiene permiso para rechazar propuestas.'}, status=status.HTTP_403_FORBIDDEN)

        if propuesta.rechazar(request.user, comentarios=comentarios):
            serializer = self.get_serializer(propuesta)
            return Response(serializer.data)
        else:
            # Actualizar el mensaje de error para reflejar los estados permitidos
            allowed_statuses_for_rejection = [
                PropuestaCompra.ESTADO_PENDIENTE_APROBACION,
                PropuestaCompra.ESTADO_APROBADA,
                PropuestaCompra.ESTADO_MODIFICADA_APROBADA
            ]
            allowed_statuses_display = [dict(PropuestaCompra.ESTADOS_CHOICES).get(s) for s in allowed_statuses_for_rejection]
            return Response(
                {'error': f'La propuesta solo puede ser rechazada si su estado es uno de los siguientes: {", ".join(filter(None, allowed_statuses_display))}. Estado actual: {propuesta.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    # New action to mark as sent to supplier
    @action(detail=True, methods=['POST'], url_path='enviar-proveedor')
    def enviar_proveedor(self, request, pk=None):
        """Marca una propuesta aprobada como enviada al proveedor."""
        propuesta = self.get_object()
        
        # Validar que la propuesta pertenezca al usuario que la envía (o es admin)
        if propuesta.comprador != request.user and not request.user.is_staff:
             return Response(
                 {'error': 'No tiene permiso para enviar esta propuesta al proveedor.'},
                 status=status.HTTP_403_FORBIDDEN
             )
             
        if propuesta.enviar_proveedor():
             serializer = self.get_serializer(propuesta)
             return Response(serializer.data)
        else:
             return Response(
                 {'error': 'Solo las propuestas aprobadas o modificadas y aprobadas pueden ser marcadas como enviadas al proveedor.'},
                 status=status.HTTP_400_BAD_REQUEST
             )

    # Override update to handle status transitions
    def update(self, request, *args, **kwargs):
        propuesta = self.get_object()
        original_estado = propuesta.estado
        is_manager = request.user.is_staff # Simple check, adjust role logic if needed
        is_buyer = propuesta.comprador == request.user
        
        # Perform the standard update first
        response = super().update(request, *args, **kwargs)
        
        # Check response status before proceeding
        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            return response
            
        # Refresh instance after update
        propuesta.refresh_from_db()
        new_estado = propuesta.estado
        
        # Apply status logic *after* successful update
        # Manager modifies a pending proposal -> modificada_aprobada
        if is_manager and original_estado == PropuestaCompra.ESTADO_PENDIENTE_APROBACION and new_estado == original_estado:
            propuesta.estado = PropuestaCompra.ESTADO_MODIFICADA_APROBADA
            # Optionally: update usuario_aprobador and date?
            propuesta.usuario_aprobador = request.user
            propuesta.fecha_aprobacion_rechazo = timezone.now()
            propuesta.save()
            # Re-serialize with the final status
            response.data = self.get_serializer(propuesta).data 

        # Buyer modifies an approved/modified proposal -> borrador
        elif is_buyer and original_estado in [PropuestaCompra.ESTADO_APROBADA, PropuestaCompra.ESTADO_MODIFICADA_APROBADA] and new_estado == original_estado:
            propuesta.estado = PropuestaCompra.ESTADO_BORRADOR
            # Clear approval fields
            propuesta.usuario_aprobador = None
            propuesta.fecha_aprobacion_rechazo = None
            propuesta.save()
            # Re-serialize with the final status
            response.data = self.get_serializer(propuesta).data
            
        return response

    # Override partial_update similarly
    def partial_update(self, request, *args, **kwargs):
        propuesta = self.get_object()
        original_estado = propuesta.estado
        is_manager = request.user.is_staff # Simple check, adjust role logic if needed
        is_buyer = propuesta.comprador == request.user
        
        # Perform the standard partial update first
        response = super().partial_update(request, *args, **kwargs)

        # Check response status before proceeding
        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            return response

        # Refresh instance after update
        propuesta.refresh_from_db()
        new_estado = propuesta.estado

        # Apply status logic *after* successful update
        # Manager modifies a pending proposal -> modificada_aprobada
        if is_manager and original_estado == PropuestaCompra.ESTADO_PENDIENTE_APROBACION and new_estado == original_estado:
            propuesta.estado = PropuestaCompra.ESTADO_MODIFICADA_APROBADA
            propuesta.usuario_aprobador = request.user
            propuesta.fecha_aprobacion_rechazo = timezone.now()
            propuesta.save()
            response.data = self.get_serializer(propuesta).data

        # Buyer modifies an approved/modified proposal -> borrador
        elif is_buyer and original_estado in [PropuestaCompra.ESTADO_APROBADA, PropuestaCompra.ESTADO_MODIFICADA_APROBADA] and new_estado == original_estado:
            propuesta.estado = PropuestaCompra.ESTADO_BORRADOR
            propuesta.usuario_aprobador = None
            propuesta.fecha_aprobacion_rechazo = None
            propuesta.save()
            response.data = self.get_serializer(propuesta).data

        return response

    @action(detail=True, methods=['POST'])
    def crear_orden_compra(self, request, pk=None):
        """
        Crea una orden de compra en Odoo basada en los items de la propuesta
        
        Se espera un payload con la siguiente estructura:
        {
            "partner_id": 2433,  # ID del proveedor en Odoo
            "currency_id": 3,    # ID de la moneda en Odoo, opcional 3
            "partner_ref": "Test 001",  # Referencia del proveedor (opcional)
            "date_order": "2025-04-30",  # Fecha de la orden (opcional)
            "picking_type_id": 7,  # Tipo de recepcion picking_type_id
            "user_id": 0,  # ID del usuario en Odoo obligatorio
            "product_mapping": {  # Mapeo de cu00f3digos de productos a IDs en Odoo (opcional)
                "DISC100": 1633784, # ID del producto en Odoo product_id
                "DISC14X3/32X1": 1816768
            }
        }
        """
        propuesta = self.get_object()
        
        # Verificar que la propuesta estu00e9 aprobada
        if propuesta.estado not in [PropuestaCompra.ESTADO_APROBADA, PropuestaCompra.ESTADO_MODIFICADA_APROBADA]:
            return Response(
                {'error': f'Solo se pueden crear u00f3rdenes de compra para propuestas aprobadas. Estado actual: {propuesta.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que haya items en la propuesta
        items = propuesta.items.filter(cantidad_propuesta__gt=0)  # Solo items con cantidad > 0
        if not items.exists():
            return Response(
                {"detail": "No se puede crear una orden de compra para una propuesta sin items con cantidad propuesta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener los datos necesarios del request
        partner_id = request.data.get('partner_id')
        
        # Obtener el nombre del comprador para construir el partner_ref
        comprador_nombre = ''
        try:
            if propuesta.comprador and hasattr(propuesta.comprador, 'profile'):
                if propuesta.comprador.profile.nombre_comprador:
                    comprador_nombre = propuesta.comprador.profile.nombre_comprador
                else:
                    comprador_nombre = propuesta.comprador.get_full_name()
            
            if not comprador_nombre and propuesta.comprador:
                comprador_nombre = propuesta.comprador.get_full_name() or propuesta.comprador.username
        except Exception as e:
            logger.warning(f"Error al obtener el nombre del comprador: {str(e)}")
            comprador_nombre = 'C'  # Valor por defecto si hay error
        
        # Obtener la primera letra del nombre del comprador para usarla en el partner_ref
        primera_letra = comprador_nombre[0].upper() if comprador_nombre else 'C'
        # El partner_ref se construiru00e1 dentro del bucle para cada proveedor
        partner_ref_from_request = request.data.get('partner_ref')
        
        # Usar la fecha actual + 1 día para compensar el problema de zona horaria en Odoo
        date_order = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        picking_type_id = request.data.get('picking_type_id', 7)
        
        # Siempre usar el odoo_user_id del perfil del comprador, ignorando el user_id del payload
        # Verificar que el comprador tenga perfil
        if not propuesta.comprador:
            error_msg = "La propuesta no tiene un comprador asignado"
            logger.error(error_msg)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
        if not hasattr(propuesta.comprador, 'profile'):
            error_msg = f"El comprador {propuesta.comprador.id} no tiene perfil"
            logger.error(error_msg)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
        # Obtener el odoo_user_id del perfil del comprador
        user_id = propuesta.comprador.profile.odoo_user_id
        
        # Verificar que el comprador tenga odoo_user_id configurado
        if not user_id:
            error_msg = f"El comprador {propuesta.comprador.id} no tiene odoo_user_id configurado en su perfil"
            logger.error(error_msg)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
        # Asegurarse de que user_id sea un entero
        try:
            user_id = int(user_id)
            logger.info(f"Usando odoo_user_id {user_id} del perfil del comprador {propuesta.comprador.id}")
        except (ValueError, TypeError):
            error_msg = f"El odoo_user_id '{user_id}' del comprador {propuesta.comprador.id} no es un entero válido"
            logger.error(error_msg)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
        product_mapping = request.data.get('product_mapping', {})  # Mapeo de cu00f3digos a IDs de Odoo
        
        if not partner_id:
            return Response(
                {"detail": "Se requiere el ID del proveedor (partner_id)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Agrupar items por proveedor_id si se especifica
        items_por_proveedor = {}
        for item in items:
            if item.proveedor_id is not None:
                if item.proveedor_id not in items_por_proveedor:
                    items_por_proveedor[item.proveedor_id] = []
                items_por_proveedor[item.proveedor_id].append(item)
            else:
                # Si no tiene proveedor_id, usar el proveedor principal
                if partner_id not in items_por_proveedor:
                    items_por_proveedor[partner_id] = []
                items_por_proveedor[partner_id].append(item)
        
        resultados = []
        successful_odoo_creations = 0 # Counter for successful Odoo PO creations
        
        # Crear una orden de compra por cada proveedor
        for proveedor_id, items_proveedor in items_por_proveedor.items():
            # Construir el partner_ref para este proveedor específico
            if partner_ref_from_request:
                partner_ref = partner_ref_from_request
                logger.info(f"Usando partner_ref del request: {partner_ref}")
            else:
                # Construir un partner_ref u00fanico para este proveedor
                partner_ref = f"{primera_letra}{propuesta.id}-{proveedor_id}"
                logger.info(f"Generando partner_ref para proveedor {proveedor_id}: {partner_ref}") 
                        # Preparar las lu00edneas de la orden
            order_lines = []
            for item in items_proveedor:
                # Obtener el ID del producto en Odoo del item o del mapeo
                product_id = item.product_id
                
                # Si no hay product_id en el item, intentar obtenerlo del mapeo
                if product_id is None or product_id == 0:
                    product_id = product_mapping.get(item.codigo)
                    
                    # Si tampoco hay mapeo, intentar convertir el cu00f3digo a entero (si es un ID)
                    if product_id is None:
                        try:
                            # Intentar usar el cu00f3digo como ID si es numu00e9rico
                            if item.codigo.isdigit():
                                product_id = int(item.codigo)
                            else:
                                # Si no es numu00e9rico, usar un ID por defecto
                                product_id = 0  # Este valor deberu00eda ser reemplazado con un ID vu00e1lido
                        except (ValueError, AttributeError):
                            product_id = 0  # Este valor deberu00eda ser reemplazado con un ID vu00e1lido
                
                # Obtener el ID de la unidad de medida del item o usar un valor por defecto
                product_uom = item.medida_id if item.medida_id is not None else 3  # Usar medida_id del item o 3 por defecto
                
                # Fecha planeada (10 du00edas despuu00e9s de la fecha actual)
                date_planned = request.data.get('date_planned', (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d'))
                
                order_line = [
                    0, 0, {
                        "name": f"[{item.codigo}] {item.producto}",
                        "product_id": product_id,
                        "product_uom": product_uom,  # Usar la unidad de medida del item
                        "product_qty": float(item.cantidad_propuesta),
                        "price_unit": float(item.costo),
                        "date_planned": date_planned,
                        "taxes_id": [(6, 0, [12])]
                    }
                ]
                order_lines.append(order_line)
            
            # Obtener el currency_id de los items (usar el primero que encontremos, o 3 por defecto)
            item_currency_id = 34  # Default: MXN
            for item in items_proveedor:
                if item.currency_id is not None:
                    item_currency_id = item.currency_id
                    break
            
            # Generar una nota estructurada con informacion de la propuesta
            notes = []
            notes.append("META DATOS DE LA PROPUESTA DE COMPRA")
            notes.append(f"ID de Propuesta: {propuesta.id}")
            notes.append(f"Fecha de creacion: {propuesta.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Informaciu00f3n del comprador
            notes.append("\nINFORMACION DEL COMPRADOR:")
            if propuesta.comprador:
                notes.append(f"ID: {propuesta.comprador.id}")
                notes.append(f"Nombre: {propuesta.comprador.get_full_name() or propuesta.comprador.username}")
                notes.append(f"Email: {propuesta.comprador.email}")
                if hasattr(propuesta.comprador, 'profile') and propuesta.comprador.profile:
                    if propuesta.comprador.profile.nombre_comprador:
                        notes.append(f"Nombre de comprador: {propuesta.comprador.profile.nombre_comprador}")
                    if propuesta.comprador.profile.telefono:
                        notes.append(f"Teléfono: {propuesta.comprador.profile.telefono}")
            else:
                notes.append("No hay informacion disponible del comprador")
            
            # Informacion de la propuesta
            notes.append("\nINFORMACION DE LA PROPUESTA:")
            if propuesta.categoria_nombre:
                notes.append(f"Categoría: {propuesta.categoria_nombre}")
            if propuesta.almacenes_ids:
                almacenes = [a.get('name', 'Sin nombre') for a in propuesta.almacenes_ids if isinstance(a, dict) and 'name' in a]
                notes.append(f"Almacenes: {', '.join(almacenes)}")
            
            # Informacion de los items
            notes.append(f"\nINFORMACION DE LOS ITEMS:")
            notes.append(f"Proveedor: {proveedor_id}")
            notes.append(f"Cantidad de items: {len(items_proveedor)}")
            
            # Lista de items
            for i, item in enumerate(items_proveedor, 1):
                notes.append(f"\nItem {i}:")
                notes.append(f"Código: {item.codigo}")
                notes.append(f"Producto: {item.producto}")
                notes.append(f"Cantidad: {item.cantidad_propuesta}")
                notes.append(f"Precio unitario: {item.costo}")
            
            # Fecha y hora actual
            current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            notes.append(f"\nFecha y hora de envío a Odoo: {current_time}")
            
            # Unir todas las notas en un solo texto
            note_text = "\n".join(notes)
            
            # Preparar los datos para la API de Odoo exactamente en el formato requerido
            data_odoo = { # Renamed to data_odoo to avoid conflict with outer 'data'
                "fields": ["name", "partner_id", "partner_ref"],
                "values": {
                    "partner_id": proveedor_id,
                    "currency_id": item_currency_id,
                    "partner_ref": partner_ref,
                    "date_order": date_order,
                    "picking_type_id": picking_type_id,
                    "user_id": user_id,
                    "order_line": order_lines,
                    "note": note_text
                }
            }
            
            try:
                # Call the actual Odoo service
                resultado_odoo = OdooService.create_purchase_order( 
                    data=data_odoo,
                    user=request.user,
                    unit_name=request.user.unidad.nombre_corto if hasattr(request.user, 'unidad') and request.user.unidad else None
                )
                # Assuming success if no exception is raised
                successful_odoo_creations += 1
                resultados.append({
                    'proveedor_id': proveedor_id,
                    'status': 'success',
                    'data': resultado_odoo # Store the actual response
                })

            except (OdooAuthError, OdooApiError) as e: # Use direct import
                logger.error(f"Odoo API error for proveedor {proveedor_id} in propuesta {propuesta.id}: {str(e)}")
                resultados.append({
                    'proveedor_id': proveedor_id,
                    'status': 'error',
                    'error': str(e) # The error message from OdooAuthError/OdooApiError
                })
            except Exception as e: # Catch other unexpected errors
                logger.error(f"Unexpected error creating Odoo order for proveedor {proveedor_id} in propuesta {propuesta.id}: {str(e)}", exc_info=True)
                resultados.append({
                    'proveedor_id': proveedor_id,
                    'status': 'error',
                    'error': f"Error inesperado: {str(e)}"
                })
        
        # After the loop, update the PropuestaCompra only if all Odoo POs were created successfully
        # and there were Odoo calls made.
        no_odoo_errors = not any(r['status'] == 'error' for r in resultados)
        
        # Procesar y formatear la respuesta de Odoo antes de guardarla
        formatted_resultados = []
        for resultado in resultados:
            if resultado.get('status') == 'success' and 'data' in resultado:
                try:
                    # Extraer y formatear la informaciu00f3n relevante
                    result_data = resultado.get('data', {}).get('result', [])[0]
                    if result_data:
                        import json
                        # Intentar parsear el resultado como JSON
                        result_json = json.loads(result_data)
                        new_resource = result_json.get('New resource', [])[0]
                        if new_resource:
                            # Guardar solo la informaciu00f3n relevante
                            formatted_resultados.append({
                                'proveedor_id': resultado.get('proveedor_id'),
                                'order_id': new_resource.get('id'),
                                'order_name': new_resource.get('name'),
                                'partner_ref': new_resource.get('partner_ref'),
                                'partner_id': new_resource.get('partner_id')[0] if isinstance(new_resource.get('partner_id'), list) else new_resource.get('partner_id'),
                                'partner_name': new_resource.get('partner_id')[1] if isinstance(new_resource.get('partner_id'), list) else None
                            })
                        else:
                            # Si no se puede extraer New resource, guardar el resultado original
                            formatted_resultados.append({
                                'proveedor_id': resultado.get('proveedor_id'),
                                'raw_result': result_json
                            })
                except Exception as e:
                    logger.error(f"Error procesando resultado de Odoo: {str(e)}")
                    # En caso de error, guardar el resultado original
                    formatted_resultados.append({
                        'proveedor_id': resultado.get('proveedor_id'),
                        'status': 'error_processing',
                        'error': str(e),
                        'raw_data': resultado.get('data')
                    })
            else:
                # Si no es success o no tiene data, guardar tal cual
                formatted_resultados.append(resultado)
        
        # Guardar solo el arreglo de objetos en odoo_response, sin los metadatos adicionales
        propuesta.odoo_response = formatted_resultados
        
        if successful_odoo_creations > 0 and no_odoo_errors:
            propuesta.estado = PropuestaCompra.ESTADO_REGISTRADA_ODOO
            propuesta.fecha_registro_odoo = timezone.now()
            
            # Preparar un comentario detallado con las órdenes organizadas por proveedor
            comentario_detalles = []
            for r in formatted_resultados:
                if r.get('order_name') and r.get('partner_name'):
                    comentario_detalles.append(f"Proveedor: {r.get('partner_name')} - PO: {r.get('order_name')}")
                elif r.get('order_name'):
                    comentario_detalles.append(f"PO: {r.get('order_name')}")
            
            comentario_base = "Orden de compra registrada en Odoo."
            if comentario_detalles:
                comentario_final = f"{comentario_base} {'; '.join(comentario_detalles)}."
            else:
                comentario_final = f"{comentario_base}"
            
            # Agregar evento al historial
            evento = {
                'accion': f"{propuesta.get_estado_display()} -> {PropuestaCompra.ESTADO_REGISTRADA_ODOO}",
                'timestamp': timezone.now().isoformat(),
                'comentario': comentario_final,
                'tipo_accion': "registro_odoo",
                'usuario_id': request.user.id,
                'usuario_nombre': request.user.get_full_name() or request.user.username
            }
            
            # Obtener el historial actual y agregar el nuevo evento
            historial_actual = propuesta.historial_eventos or []
            historial_actual.append(evento)
            propuesta.historial_eventos = historial_actual
            
            try:
                update_fields_list = ['estado', 'fecha_registro_odoo', 'odoo_response', 'historial_eventos']
                # Extraer y guardar el ID de la orden de compra de Odoo si está disponible
                if formatted_resultados and len(formatted_resultados) == 1 and 'order_id' in formatted_resultados[0]:
                    # Si solo hay un resultado formateado, podemos guardar el ID directamente
                    propuesta.odoo_purchase_order_id = str(formatted_resultados[0]['order_id'])
                    update_fields_list.append('odoo_purchase_order_id')
                    logger.info(f"Saved Odoo purchase order ID {propuesta.odoo_purchase_order_id} for propuesta {propuesta.id}")
                elif formatted_resultados and len(formatted_resultados) > 1:
                    # Si hay múltiples resultados, guardar una lista de IDs separados por comas
                    order_ids = [str(r.get('order_id')) for r in formatted_resultados if r.get('order_id')]
                    if order_ids:
                        propuesta.odoo_purchase_order_id = ','.join(order_ids)
                        update_fields_list.append('odoo_purchase_order_id')
                        logger.info(f"Saved multiple Odoo purchase order IDs {propuesta.odoo_purchase_order_id} for propuesta {propuesta.id}")
                
                propuesta.save(update_fields=update_fields_list)
                logger.info(f"Propuesta {propuesta.id} status updated to REGISTRADA_ODOO as all Odoo operations were successful.")
            except Exception as e_save:
                logger.error(f"Error saving Propuesta {propuesta.id} after successful Odoo registration: {str(e_save)}")
        elif successful_odoo_creations > 0 and not no_odoo_errors:
            # Guardar la respuesta aunque haya habido errores
            try:
                propuesta.save(update_fields=['odoo_response'])
                logger.info(f"Saved Odoo response for propuesta {propuesta.id} despite errors")
            except Exception as e_save:
                logger.error(f"Error saving Odoo response for Propuesta {propuesta.id}: {str(e_save)}")
            logger.warning(f"Propuesta {propuesta.id} had {successful_odoo_creations} successful Odoo creations but also errors. Status NOT changed to REGISTRADA_ODOO.")
        
        # Check if any Odoo operation resulted in an error to determine HTTP status
        any_odoo_error_overall = any(r['status'] == 'error' for r in resultados)

        if any_odoo_error_overall:
            first_error_message = "One or more Odoo operations failed."
            for r_item in resultados:
                if r_item['status'] == 'error' and r_item.get('error'):
                    first_error_message = f"Odoo operation failed: {str(r_item.get('error'))}"
                    break 
            
            return Response({
                'propuesta_id': propuesta.id,
                'resultados': resultados,
                'message': first_error_message
            }, status=status.HTTP_400_BAD_REQUEST)

        # If no errors overall, return 200 OK
        final_message = f"Odoo operations for propuesta {propuesta.id} completed."
        if not items_por_proveedor and not resultados: # No items were attempted for Odoo processing
            final_message = f"No items to process for Odoo order creation for propuesta {propuesta.id}."
        elif successful_odoo_creations == len(items_por_proveedor) and successful_odoo_creations > 0:
             final_message = f"All {successful_odoo_creations} Odoo purchase order(s) created successfully for propuesta {propuesta.id}."
        elif not resultados and items_por_proveedor: # Items were attempted but 'resultados' is empty (should not happen if loop runs)
            final_message = f"Odoo processing attempted for propuesta {propuesta.id}, but no results were recorded."


        return Response({
            'propuesta_id': propuesta.id,
            'resultados': resultados,
            'message': final_message
        })

# --- Items --- #

class ItemPropuestaCompraViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar items de propuestas de compra
    """
    queryset = ItemPropuestaCompra.objects.all()
    serializer_class = ItemPropuestaCompraSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ItemPropuestaCompra.objects.all()
        
        # Filtrar por propuesta si se especifica
        propuesta_id = self.request.query_params.get('propuesta_id', None)
        if propuesta_id:
            queryset = queryset.filter(propuesta_id=propuesta_id)
            
        # Filtrar por código de producto si se especifica
        codigo = self.request.query_params.get('codigo', None)
        if codigo:
            queryset = queryset.filter(codigo=codigo)
            
        # Filtrar por categoría si se especifica
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo item para una propuesta de compra existente
        """
        # Obtener la propuesta asociada
        propuesta_id = request.data.get('propuesta')
        try:
            propuesta = PropuestaCompra.objects.get(pk=propuesta_id)
            
            # Verificar que la propuesta esté en estado borrador
            if propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
                return Response(
                    {"detail": f"No se pueden agregar items a una propuesta que no esté en estado borrador. Estado actual: {propuesta.get_estado_display()}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Continuar con la creación normal
            return super().create(request, *args, **kwargs)
        except PropuestaCompra.DoesNotExist:
            return Response(
                {"detail": "Propuesta no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, *args, **kwargs):
        """
        Actualiza un item de propuesta de compra existente (PUT)
        """
        instance = self.get_object()
        propuesta = instance.propuesta
        
        # Verificar que la propuesta esté en estado borrador
        if propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
            return Response(
                {"detail": f"No se pueden modificar items de una propuesta que no esté en estado borrador. Estado actual: {propuesta.get_estado_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Continuar con la actualización normal
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente un item de propuesta de compra existente (PATCH)
        """
        instance = self.get_object()
        propuesta = instance.propuesta
        
        # Verificar que la propuesta esté en estado borrador
        if propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
            return Response(
                {"detail": f"No se pueden modificar items de una propuesta que no esté en estado borrador. Estado actual: {propuesta.get_estado_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Continuar con la actualización parcial normal
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Elimina un item de propuesta de compra existente
        """
        instance = self.get_object()
        propuesta = instance.propuesta
        
        # Verificar que la propuesta esté en estado borrador
        if propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
            return Response(
                {"detail": f"No se pueden eliminar items de una propuesta que no esté en estado borrador. Estado actual: {propuesta.get_estado_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Continuar con la eliminación normal
        return super().destroy(request, *args, **kwargs)
        
    @action(detail=False, methods=['PATCH'])
    def bulk_update(self, request):
        """
        Actualiza múltiples items de una propuesta en una sola operación
        
        Ejemplo de payload:
        {
            "propuesta_id": 1,
            "items": [
                {"id": 1, "propuesta": 5, "comentarios": "Nuevo comentario"},
                {"id": 2, "proveedor": "Nuevo proveedor"}
            ]
        }
        """
        propuesta_id = request.data.get('propuesta_id')
        items_data = request.data.get('items', [])
        
        if not propuesta_id or not items_data:
            return Response(
                {"detail": "Se requiere propuesta_id y al menos un item para actualizar"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            propuesta = PropuestaCompra.objects.get(pk=propuesta_id)
            
            # Verificar que la propuesta esté en estado borrador
            if propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
                return Response(
                    {"detail": f"No se pueden modificar items de una propuesta que no esté en estado borrador. Estado actual: {propuesta.get_estado_display()}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            results = []
            for item_data in items_data:
                item_id = item_data.get('id')
                if not item_id:
                    continue  # Ignorar items sin ID
                    
                try:
                    item = ItemPropuestaCompra.objects.get(pk=item_id, propuesta=propuesta)
                    serializer = self.get_serializer(item, data=item_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        results.append({
                            'id': item_id,
                            'status': 'success',
                            'data': serializer.data
                        })
                    else:
                        results.append({
                            'id': item_id,
                            'status': 'error',
                            'errors': serializer.errors
                        })
                except ItemPropuestaCompra.DoesNotExist:
                    results.append({
                        'id': item_id,
                        'status': 'error',
                        'detail': 'Item no encontrado'
                    })
                    
            return Response({
                'propuesta_id': propuesta_id,
                'results': results
            })
                
        except PropuestaCompra.DoesNotExist:
            return Response(
                {"detail": "Propuesta no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['POST'])
    def update_proveedores(self, request):
        """
        Actualiza los proveedores y monedas de múltiples items en una sola operación
        
        Ejemplo de payload:
        {
            "items": [
                {"id": 1, "proveedor_id": 123, "currency_id": 1},
                {"id": 2, "proveedor_id": 456, "currency_id": 2}
            ]
        }
        """
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response(
                {"detail": "Se requieren items para actualizar"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        for item_data in items_data:
            item_id = item_data.get('id')
            proveedor_id = item_data.get('proveedor_id')
            currency_id = item_data.get('currency_id')
            
            if not item_id or proveedor_id is None:
                results.append({
                    'id': item_id,
                    'status': 'error',
                    'detail': 'Se requiere id y proveedor_id'
                })
                continue
                
            try:
                item = ItemPropuestaCompra.objects.get(pk=item_id)
                # Permitimos actualizar el proveedor y moneda independientemente del estado de la propuesta
                item.proveedor_id = proveedor_id
                
                # Lista de campos a actualizar
                update_fields = ['proveedor_id', 'fecha_actualizacion']
                
                # Actualizar currency_id si se proporcionó en la solicitud
                if currency_id is not None:
                    item.currency_id = currency_id
                    update_fields.append('currency_id')
                    
                item.save(update_fields=update_fields)
                
                result = {
                    'id': item_id,
                    'status': 'success',
                    'proveedor_id': proveedor_id
                }
                
                if currency_id is not None:
                    result['currency_id'] = currency_id
                    
                results.append(result)
            except ItemPropuestaCompra.DoesNotExist:
                results.append({
                    'id': item_id,
                    'status': 'error',
                    'detail': 'Item no encontrado'
                })
        
        return Response({
            'results': results
        })
