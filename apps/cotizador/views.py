import uuid
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch, Q
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime

from .models import (
    Cliente,
    Cotizacion,
    ProductoCotizacion,
    CotizadorImagenproducto,
    Kit,
    KitProducto
)
from .serializers import (
    ClienteSerializer,
    CotizacionSerializer,
    ProductoCotizacionSerializer,
    CotizadorImagenproductoSerializer,
    KitSerializer,
    KitCreateUpdateSerializer,
    KitProductoSerializer,
    KitProductoCreateUpdateSerializer,
    ApplyKitToCotizacionSerializer,
    KitImageUploadSerializer,
    CreateOrderSerializer
)
from .services import OdooService, DecimalEncoder
from .utils.upload_helpers import upload_kit_image_to_supabase, upload_kit_image_without_uuid
from .cache.tasks import sync_products_task
from .cache.sync import sync_products_to_supabase, get_clients_from_supabase
from .pagination import CustomPageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
import copy


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Cliente.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name_partner__icontains=search) |
                Q(rfc__icontains=search)
            )
        return queryset

class CotizacionViewSet(viewsets.ModelViewSet):
    # Verificar si los campos de usuario existen en la base de datos
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(
        """SELECT column_name FROM information_schema.columns 
           WHERE table_name = 'cotizador_cotizacion' 
           AND column_name = 'usuario_creacion_id'"""
    )
    usuario_fields_exist = bool(cursor.fetchone())
    
    queryset = Cotizacion.objects.all()
    serializer_class = CotizacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['folio', 'proyecto', 'cliente']
    
    def create(self, request, *args, **kwargs):
        print("=== DATOS RECIBIDOS AL CREAR COTIZACIÓN ===")
        print("Headers:", request.headers)
        print("User:", request.user.email if request.user.is_authenticated else 'No autenticado')
        print("Data:", request.data)
        print("Query Params:", request.query_params)
        print("========================================")
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Cotizacion.objects.all()
        # Filtros existentes
        estatus = self.request.query_params.get('estatus', None)
        if estatus:
            queryset = queryset.filter(estatus=estatus)
        cliente_id = self.request.query_params.get('cliente', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        fecha_fin = self.request.query_params.get('fecha_fin', None)
        if fecha_inicio:
            queryset = queryset.filter(fecha_creacion__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_creacion__lte=fecha_fin)
            
        # Nuevos filtros por usuario (solo si los campos existen)
        if self.__class__.usuario_fields_exist:
            usuario_id = self.request.query_params.get('usuario_id', None)
            usuario_email = self.request.query_params.get('usuario_email', None)
            
            # Filtrar por ID de usuario
            if usuario_id:
                queryset = queryset.filter(usuario_creacion_id=usuario_id)
            
            # Filtrar por email de usuario
            if usuario_email:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    usuario = User.objects.get(email=usuario_email)
                    queryset = queryset.filter(usuario_creacion=usuario)
                except User.DoesNotExist:
                    # Si no existe el usuario, devolver queryset vacío
                    queryset = queryset.none()
                
        return queryset

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get('estatus', instance.estatus)
        
        # Actualizar usuario según el cambio de estatus (solo si los campos existen)
        if new_status != instance.estatus and self.__class__.usuario_fields_exist:
            if new_status == 'enviada':
                serializer.save(usuario_envio=self.request.user)
            elif new_status == 'aprobada':
                serializer.save(usuario_aprobacion=self.request.user)
            elif new_status == 'rechazada':
                serializer.save(usuario_rechazo=self.request.user)
            else:
                serializer.save()
        else:
            serializer.save()

    def perform_create(self, serializer):
        # Datos iniciales para guardar
        save_kwargs = {}
        user = self.request.user
        
        # Si el campo de usuario existe, asignar el usuario creador
        if self.__class__.usuario_fields_exist:
            save_kwargs['usuario_creacion'] = user
        
        # Obtener el vendedor_id del payload si existe
        vendedor_id = self.request.data.get('vendedor_id')
        
        if vendedor_id:
            print(f"Vendedor ID recibido del frontend: {vendedor_id}")
            
            # Guardar el vendedor_id en el perfil del usuario si no lo tiene
            if not user.vendedor_id:
                user.vendedor_id = vendedor_id
                user.save(update_fields=['vendedor_id'])
                print(f"Vendedor ID {vendedor_id} guardado en el perfil del usuario {user.email}")
            
            # Usar el vendedor_id del payload para la cotización
            save_kwargs['vendedor_id'] = vendedor_id
            print(f"Asignando vendedor_id: {vendedor_id} a la cotización")
        
        # Guardar la cotización con los parámetros
        serializer.save(**save_kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, *args, **kwargs):
        cotizacion = self.get_object()
        nueva_cotizacion = Cotizacion.objects.get(pk=cotizacion.pk)
        nueva_cotizacion.pk = None
        nueva_cotizacion.uuid = uuid.uuid4()
        nueva_cotizacion.save()

        # Duplicar productos
        for producto in cotizacion.productos.all():
            nuevo_producto = ProductoCotizacion.objects.get(pk=producto.pk)
            nuevo_producto.pk = None
            nuevo_producto.cotizacion = nueva_cotizacion
            nuevo_producto.save()

        serializer = self.get_serializer(nueva_cotizacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def apply_kit(self, request, uuid=None):
        """
        Aplica un kit a una cotización existente.
        
        Permite añadir todos los productos de un kit a una cotización,
        ya sea como un producto tipo kit o como productos individuales.
        """
        cotizacion = self.get_object()
        serializer = ApplyKitToCotizacionSerializer(data=request.data)
        
        if serializer.is_valid():
            kit_uuid = serializer.validated_data['kit_uuid']
            mostrar_productos_individuales = serializer.validated_data['mostrar_productos_individuales']
            porcentaje_descuento_adicional = serializer.validated_data['porcentaje_descuento_adicional']
            
            # Obtener valores personalizados si se proporcionan
            cantidad_personalizada = serializer.validated_data.get('cantidad')
            valor_unitario_personalizado = serializer.validated_data.get('valor_unitario')
            costo_unitario_personalizado = serializer.validated_data.get('costo_unitario')
            porcentaje_descuento_personalizado = serializer.validated_data.get('porcentaje_descuento')
            valor_unitario_con_descuento_personalizado = serializer.validated_data.get('valor_unitario_con_descuento')
            
            try:
                # Log de kits disponibles para depuración

                # Obtener todos los kits disponibles
                for k in Kit.objects.all():
                    pass  # Verificar disponibilidad de kits
                
                # Obtener el kit
                kit = Kit.objects.get(uuid=kit_uuid)
                
                # Verificar que el kit tenga productos
                if kit.productos.count() == 0:
                    # Si el kit no tiene productos pero tiene valores directos, los usaremos
                    if kit.valor_unitario > 0:
                        pass  # El kit tiene valores directos que podemos usar
                    else:
                        return Response({
                            'error': f'El kit "{kit.nombre}" no tiene productos asociados ni valores directos'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calcular los totales del kit basados en sus productos
                precio_lista_total = Decimal('0')
                costo_total = Decimal('0')
                precio_descuento_total = Decimal('0')
                
                # Sumar los valores de todos los productos del kit
                for producto_kit in kit.productos.all():
                    # Procesar producto del kit
                    
                    precio_lista_total += producto_kit.precio_lista
                    costo_total += producto_kit.costo
                    
                    # Aplicar descuento adicional al precio con descuento del producto
                    precio_descuento_producto = producto_kit.precio_descuento
                    if porcentaje_descuento_adicional > 0:
                        precio_descuento_producto = precio_descuento_producto * (Decimal(100) - porcentaje_descuento_adicional) / Decimal(100)
                        # Aplicar descuento adicional
                    
                    precio_descuento_total += precio_descuento_producto
                
                # Calcular el descuento total efectivo
                if precio_lista_total > 0:
                    descuento_total = (Decimal(100) - (precio_descuento_total * Decimal(100) / precio_lista_total))
                else:
                    descuento_total = kit.porcentaje_descuento
                    if porcentaje_descuento_adicional > 0:
                        descuento_total = Decimal(100) - ((Decimal(100) - kit.porcentaje_descuento) * \
                                                      (Decimal(100) - porcentaje_descuento_adicional) / Decimal(100))
                
                # Usar la cantidad personalizada si se proporciona, de lo contrario usar la cantidad del kit
                cantidad_total = cantidad_personalizada if cantidad_personalizada is not None else kit.cantidad
                # Usar cantidad personalizada o predeterminada
                
                # Usar valores personalizados si se proporcionan
                if valor_unitario_personalizado is not None:
                    precio_lista_total = valor_unitario_personalizado
                    # Usar valor unitario personalizado
                    
                if costo_unitario_personalizado is not None:
                    costo_total = costo_unitario_personalizado
                    # Usar costo unitario personalizado
                    
                if porcentaje_descuento_personalizado is not None:
                    descuento_total = porcentaje_descuento_personalizado
                    # Usar porcentaje de descuento personalizado
                    
                if valor_unitario_con_descuento_personalizado is not None:
                    precio_descuento_total = valor_unitario_con_descuento_personalizado
                    # Usar valor unitario con descuento personalizado
                    
                # Calcular el importe basado en el precio con descuento y la cantidad
                importe = precio_descuento_total
                
                # Si los totales calculados son 0, usar los valores del kit directamente
                if precio_lista_total == 0 and kit.valor_unitario > 0:
                    # Usar valores del kit directamente porque los totales calculados son 0
                    precio_lista_total = kit.costo_unitario
                    costo_total = kit.costo_unitario
                    precio_descuento_total = kit.valor_unitario_con_descuento
                    importe = precio_descuento_total

                
                # Asegurar que los valores sean Decimal y no None
                precio_lista_total = Decimal(precio_lista_total) if precio_lista_total is not None else Decimal('0')
                costo_total = Decimal(costo_total) if costo_total is not None else Decimal('0')
                precio_descuento_total = Decimal(precio_descuento_total) if precio_descuento_total is not None else Decimal('0')
                importe = Decimal(importe) if importe is not None else Decimal('0')
                
                # Crear el producto de cotización para el kit (sin agregar productos individuales)
                try:
                    # Asegurarnos que los valores sean Decimal antes de usarlos
                    precio_lista_total = Decimal(str(precio_lista_total)) if precio_lista_total is not None else Decimal('0')
                    costo_total = Decimal(str(costo_total)) if costo_total is not None else Decimal('0')
                    precio_descuento_total = Decimal(str(precio_descuento_total)) if precio_descuento_total is not None else Decimal('0')
                    importe = Decimal(str(importe)) if importe is not None else Decimal('0')
                    descuento_total = Decimal(str(descuento_total)) if descuento_total is not None else Decimal('0')
                    
                    # Imprimir información de depuración
                    print(f"Creando kit en cotización {cotizacion.uuid}:")
                    print(f"  Kit UUID: {kit.uuid}")
                    print(f"  Nombre: {kit.nombre}")
                    print(f"  Cantidad: {cantidad_total}")
                    print(f"  Precio lista: {precio_lista_total}")
                    print(f"  Costo: {costo_total}")
                    print(f"  Descuento: {descuento_total}%")
                    print(f"  Precio con descuento: {precio_descuento_total}")
                    print(f"  Importe: {importe}")
                    
                    # Primero verificamos si ya existe este kit en la cotización
                    kit_existente = ProductoCotizacion.objects.filter(
                        cotizacion=cotizacion,
                        kit_uuid=kit.uuid,
                        es_kit=True
                    ).first()
                    
                    if kit_existente:
                        print(f"El kit ya existe en la cotización con ID: {kit_existente.id}")
                        # Actualizar valores
                        kit_existente.cantidad += cantidad_total
                        kit_existente.porcentaje_descuento = descuento_total
                        kit_existente.precio_lista = precio_lista_total
                        kit_existente.costo = costo_total
                        kit_existente.precio_descuento = precio_descuento_total
                        kit_existente.importe = importe
                        kit_existente.mostrar_en_cotizacion = True  # Asegurar que sea visible
                        kit_existente.save()
                        producto_cotizacion = kit_existente
                        print(f"Kit actualizado con éxito. Nueva cantidad: {kit_existente.cantidad}")
                    else:
                        # Crear un nuevo producto de cotización para el kit
                        producto_cotizacion = ProductoCotizacion.objects.create(
                            cotizacion=cotizacion,
                            es_kit=True,
                            clave=kit.nombre,
                            descripcion=kit.descripcion,
                            imagen_url=kit.imagen_url,
                            tag=kit.tag,
                            cantidad=cantidad_total,
                            porcentaje_descuento=descuento_total,
                            precio_lista=precio_lista_total,
                            costo=costo_total,
                            precio_descuento=precio_descuento_total,
                            importe=importe,
                            kit_uuid=kit.uuid,
                            mostrar_en_cotizacion=True  # IMPORTANTE: Asegurar que sea visible
                        )
                        print(f"Nuevo ProductoCotizacion creado con ID: {producto_cotizacion.id}")
                    
                    # Forzar una limpieza del caché de relaciones
                    cotizacion.refresh_from_db()
                    
                    # Verificar todos los productos en la cotización
                    todos_productos = ProductoCotizacion.objects.filter(cotizacion=cotizacion).values_list('id', 'clave', 'mostrar_en_cotizacion')
                    print(f"TODOS los productos en la cotización {cotizacion.uuid}:")
                    for prod in todos_productos:
                        print(f"  ID: {prod[0]}, Clave: {prod[1]}, Mostrar: {prod[2]}")
                    
                    # Verificar si el producto fue creado correctamente
                    productos_visibles = ProductoCotizacion.objects.filter(
                        cotizacion=cotizacion,
                        mostrar_en_cotizacion=True
                    ).count()
                    print(f"Total productos VISIBLES en la cotización: {productos_visibles}")
                except Exception as e:
                    print(f"Error al crear el producto: {str(e)}")
                    return Response({
                        'error': f'Error al crear el producto: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Solo mostrar informaciu00f3n del producto si se creu00f3 exitosamente
                try:
                    # Producto cotización creado exitosamente
                    pass  # Verificar valores del producto creado
                except UnboundLocalError:
                    pass  # No se pudo acceder al producto_cotizacion
                
                # Actualizar los totales de la cotización
                try:
                    self._actualizar_totales_cotizacion(cotizacion)
                    pass  # Totales de cotización actualizados correctamente
                except Exception as e:
                    pass  # Error al actualizar totales
                
                # Actualizar los valores del kit con los totales calculados
                try:
                    if precio_lista_total > 0:
                        # Actualizando valores del kit
                        
                        kit.valor_unitario = precio_lista_total
                        kit.costo_unitario = costo_total
                        kit.porcentaje_descuento = descuento_total
                        kit.valor_unitario_con_descuento = precio_descuento_total
                        kit.save()
                        
                        pass  # Valores del kit actualizados
                except Exception as e:
                    pass  # Error al actualizar los valores del kit
                
                return Response({
                    'message': f'Kit "{kit.nombre}" aplicado correctamente a la cotización',
                    'kit_uuid': str(kit.uuid),
                    'cotizacion_uuid': str(cotizacion.uuid)
                }, status=status.HTTP_200_OK)
                
            except Kit.DoesNotExist:
                return Response({
                    'error': 'El kit especificado no existe'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Error al aplicar el kit: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _actualizar_totales_cotizacion(self, cotizacion):
        """
        Actualiza los totales de una cotización basado en sus productos.
        """
        productos = cotizacion.productos.filter(mostrar_en_cotizacion=True)
        
        # Calcular subtotal
        subtotal = sum(producto.importe for producto in productos)
        
        # Calcular descuento total
        total_descuento = sum(
            (producto.precio_lista * producto.cantidad) - producto.importe 
            for producto in productos
        )
        
        # Calcular IVA (16%)
        iva = subtotal * Decimal('0.16')
        
        # Calcular total general
        total_general = subtotal + cotizacion.logistica + iva
        
        # Actualizar cotización
        cotizacion.subtotal_mobiliario = subtotal
        cotizacion.total_descuento = total_descuento
        cotizacion.iva = iva
        cotizacion.total_general = total_general
        cotizacion.save()

class ProductoCotizacionViewSet(viewsets.ModelViewSet):
    queryset = ProductoCotizacion.objects.all()
    serializer_class = ProductoCotizacionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = ProductoCotizacion.objects.all()
        
        # Filtrar por cotización
        cotizacion_uuid = self.request.query_params.get('cotizacion_uuid', None)
        if cotizacion_uuid:
            queryset = queryset.filter(cotizacion__uuid=cotizacion_uuid)
            
        # Filtrar por ID
        producto_id = self.request.query_params.get('id', None)
        if producto_id:
            queryset = queryset.filter(id=producto_id)
            
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            # Imprimir los datos recibidos para depuración
            print('=============================================')
            print('DATOS RECIBIDOS EN LA VISTA:')
            print(f"Route ID en request.data: {request.data.get('route_id')}")
            print(f"Tipo de route_id: {type(request.data.get('route_id'))}")
            print(f"Todos los datos: {request.data}")
            print('=============================================')
            
            # Validar los datos con el serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Crear el producto
            self.perform_create(serializer)
            
            # Actualizar los totales de la cotización si se proporciona el UUID
            if 'cotizacion_uuid' in request.data:
                try:
                    cotizacion = Cotizacion.objects.get(uuid=request.data['cotizacion_uuid'])
                    cotizacion_viewset = CotizacionViewSet()
                    cotizacion_viewset._actualizar_totales_cotizacion(cotizacion)
                except Cotizacion.DoesNotExist:
                    print(f"No se encontró la cotización con UUID: {request.data['cotizacion_uuid']}")
                except Exception as e:
                    print(f"Error al actualizar totales de cotización: {str(e)}")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            print(f"Error de validación al crear producto: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            print(f"Error al crear producto: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"detail": f"Error al crear el producto: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            # No permitir cambiar la cotización
            if 'cotizacion_uuid' in request.data:
                return Response(
                    {"detail": "No se puede cambiar la cotización de un producto"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_update(serializer)
            return Response(serializer.data)
        except ProductoCotizacion.DoesNotExist:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Error al actualizar el producto"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProductoCotizacion.DoesNotExist:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": "Error al eliminar el producto"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CotizadorImagenproductoViewSet(viewsets.ModelViewSet):
    queryset = CotizadorImagenproducto.objects.all()
    serializer_class = CotizadorImagenproductoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = CotizadorImagenproducto.objects.all()
        clave_padre = self.request.query_params.get('clave_padre', None)
        if clave_padre:
            queryset = queryset.filter(clave_padre=clave_padre)
        return queryset


class KitViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Kit.
    """
    # El campo creado_por ya existe en el modelo Kit, pero verificamos para mantener consistencia
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(
        """SELECT column_name FROM information_schema.columns 
           WHERE table_name = 'cotizador_kit' 
           AND column_name = 'creado_por_id'"""
    )
    creado_por_exists = bool(cursor.fetchone())
    
    queryset = Kit.objects.all()
    serializer_class = KitSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return KitCreateUpdateSerializer
        return KitSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo kit y retorna su UUID.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Asigna el usuario actual como creador del kit.
        """
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer):
        """
        Actualiza el kit asegurándose de que todos los campos, incluido el tag, se actualicen correctamente.
        """
        # Obtener el valor del tag de los datos validados
        tag = serializer.validated_data.get('tag')
        print(f"Tag en validated_data: {tag}")
        
        # Guardar el kit con el tag actualizado
        serializer.save()
        
        # Verificar que el tag se haya guardado correctamente
        instance = serializer.instance
        print(f"Tag después de guardar: {instance.tag}")
        
        # Si el tag no se actualizó correctamente, actualizarlo directamente
        if tag is not None and instance.tag != tag:
            print(f"Actualizando tag directamente: {tag}")
            Kit.objects.filter(uuid=instance.uuid).update(tag=tag)
            # Refrescar la instancia para obtener los cambios
            instance.refresh_from_db()
            print(f"Tag después de actualización directa: {instance.tag}")

    def get_queryset(self):
        queryset = Kit.objects.all()
        
        # Filtrar por nombre
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        
        # Filtrar por usuario creador (ID)
        creado_por = self.request.query_params.get('creado_por', None)
        if creado_por:
            queryset = queryset.filter(creado_por_id=creado_por)
            
        # Nuevos filtros por usuario
        usuario_id = self.request.query_params.get('usuario_id', None)
        usuario_email = self.request.query_params.get('usuario_email', None)
        
        # El campo creado_por ya existe en el modelo Kit, así que no necesitamos verificar su existencia
        # Filtrar por ID de usuario
        if usuario_id:
            queryset = queryset.filter(creado_por_id=usuario_id)
        
        # Filtrar por email de usuario
        if usuario_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                usuario = User.objects.get(email=usuario_email)
                queryset = queryset.filter(creado_por=usuario)
            except User.DoesNotExist:
                # Si no existe el usuario, devolver queryset vacío
                queryset = queryset.none()
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        
    def update(self, request, *args, **kwargs):
        """
        Actualiza un kit y también actualiza todos los productos de cotización
        que estén asociados a este kit.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Imprimir los datos de la solicitud para depuración
        print(f"\nDatos de la solicitud: {request.data}")
        print(f"Tag en la solicitud: {request.data.get('tag')}")
        print(f"Tag actual en la instancia: {instance.tag}\n")
        
        # Guardar valores originales para comparación
        original_nombre = instance.nombre
        original_descripcion = instance.descripcion
        original_imagen_url = instance.imagen_url
        original_tag = instance.tag
        original_cantidad = instance.cantidad
        original_valor_unitario = instance.valor_unitario
        original_costo_unitario = instance.costo_unitario
        original_porcentaje_descuento = instance.porcentaje_descuento
        original_valor_unitario_con_descuento = instance.valor_unitario_con_descuento
        
        # Verificar si se está enviando el campo 'padre' en la solicitud
        padre_en_request = 'padre' in request.data
        
        # Actualizar el kit
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Imprimir valores después de la actualización para depuración
        print(f"\nTag después de la actualización: {instance.tag}\n")
        
        # Si los valores han cambiado, actualizar los productos de cotización asociados
        if (original_nombre != instance.nombre or
            original_descripcion != instance.descripcion or
            original_imagen_url != instance.imagen_url or
            original_tag != instance.tag or
            original_cantidad != instance.cantidad or
            original_valor_unitario != instance.valor_unitario or
            original_costo_unitario != instance.costo_unitario or
            original_porcentaje_descuento != instance.porcentaje_descuento or
            original_valor_unitario_con_descuento != instance.valor_unitario_con_descuento or
            padre_en_request):
            
            # Importar aquí para evitar importaciones circulares
            from apps.cotizador.models import ProductoCotizacion

            
            # Buscar todos los productos de cotización asociados a este kit
            productos_cotizacion = ProductoCotizacion.objects.filter(kit_uuid=instance.uuid, es_kit=True)
            # Actualizar productos de cotización asociados al kit
            
            # Actualizar cada producto de cotización
            for producto in productos_cotizacion:
                # Actualizar producto de cotización
                
                # Actualizar campos básicos
                if original_nombre != instance.nombre:
                    producto.clave = instance.nombre
                if original_descripcion != instance.descripcion:
                    producto.descripcion = instance.descripcion
                if original_imagen_url != instance.imagen_url:
                    producto.imagen_url = instance.imagen_url
                if original_tag != instance.tag:
                    producto.tag = instance.tag
                
                # Actualizar el campo 'padre' si se envió en la solicitud
                if padre_en_request:
                    producto.padre = request.data.get('padre')
                    print(f"Actualizando campo 'padre' a {request.data.get('padre')} para producto {producto.id}")
                
                # Actualizar cantidad si ha cambiado
                cantidad_anterior = producto.cantidad
                if original_cantidad != instance.cantidad:
                    # Actualizar cantidad
                    producto.cantidad = instance.cantidad
                    
                # Actualizar valores numéricos si han cambiado
                if original_valor_unitario != instance.valor_unitario:
                    producto.precio_lista = instance.valor_unitario
                if original_costo_unitario != instance.costo_unitario:
                    producto.costo = instance.costo_unitario
                if original_porcentaje_descuento != instance.porcentaje_descuento:
                    producto.porcentaje_descuento = instance.porcentaje_descuento
                if original_valor_unitario_con_descuento != instance.valor_unitario_con_descuento:
                    producto.precio_descuento = instance.valor_unitario_con_descuento
                
                # Asegurar que precio_descuento tenga un valor
                if producto.precio_descuento is None:
                    producto.precio_descuento = producto.precio_lista * (1 - (producto.porcentaje_descuento / 100))
                    # Calcular precio descuento
                
                # Recalcular el importe usando solo el precio_descuento (sin multiplicar por cantidad)
                # Siempre actualizar el importe cuando cualquier valor relevante cambie
                if (original_valor_unitario != instance.valor_unitario or
                    original_porcentaje_descuento != instance.porcentaje_descuento or
                    original_valor_unitario_con_descuento != instance.valor_unitario_con_descuento):
                    producto.importe = producto.precio_descuento
                
                # Guardar los cambios
                try:
                    producto.save()
                    pass  # Producto actualizado correctamente
                except Exception as e:
                    pass  # Error al actualizar producto
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente un kit y también actualiza todos los productos
        de cotización que estén asociados a este kit.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, uuid=None):
        """
        Duplica un kit existente y todos sus productos.
        """
        kit = self.get_object()
        nuevo_kit = kit.duplicar()
        
        serializer = self.get_serializer(nuevo_kit)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_product(self, request, uuid=None):
        """
        Añade un producto al kit.
        """
        kit = self.get_object()
        
        # Validamos el serializer
        serializer = KitProductoCreateUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Obtener la URL de la imagen del producto si existe
                producto_imagen = serializer.validated_data.get('producto_imagen')
                
                # El serializador ya mapea 'clave' a 'reference_mask' internamente
                producto = kit.agregar_producto(
                    orden=serializer.validated_data.get('orden', 0),
                    clave=serializer.validated_data['clave'],
                    cantidad=serializer.validated_data['cantidad'],
                    porcentaje_descuento=serializer.validated_data.get('porcentaje_descuento', 0),
                    precio_lista=serializer.validated_data.get('precio_lista', 0),
                    costo=serializer.validated_data.get('costo', 0),
                    descripcion=serializer.validated_data.get('descripcion'),
                    linea=serializer.validated_data.get('linea'),
                    familia=serializer.validated_data.get('familia'),
                    grupo=serializer.validated_data.get('grupo'),
                    tag=serializer.validated_data.get('tag'),
                    mostrar_en_kit=serializer.validated_data.get('mostrar_en_kit', True),
                    es_opcional=serializer.validated_data.get('es_opcional', False),
                    producto_id=serializer.validated_data.get('producto_id'),
                    especial=serializer.validated_data.get('especial', False),
                    padre=serializer.validated_data.get('padre'),
                    route_id=serializer.validated_data.get('route_id')
                )
                
                # Si tenemos una URL de imagen, guardarla en la tabla CotizadorImagenproducto
                if producto_imagen:
                    from .models import CotizadorImagenproducto
                    # Guardar la URL tal como viene, sin validación
                    imagen_obj, created = CotizadorImagenproducto.objects.update_or_create(
                        clave_padre=serializer.validated_data['clave'],
                        defaults={'url': producto_imagen.replace(" ", "%20")}
                    )
                
                response_serializer = KitProductoSerializer(producto)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def products(self, request, uuid=None):
        """
        Obtiene todos los productos de un kit.
        """
        kit = self.get_object()
        productos = kit.productos.all().order_by('orden')
        serializer = KitProductoSerializer(productos, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'])
    def upload_kit_image(self, request):
        """
        Sube una imagen para un kit sin requerir UUID en la URL.
        Si se proporciona un kit_uuid en los datos, se asocia la imagen a ese kit.
        """
        serializer = KitImageUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            image_file = serializer.validated_data['image']
            kit_uuid = request.data.get('kit_uuid')
            
            if kit_uuid:
                # Si se proporciona un kit_uuid, buscar el kit y asociar la imagen
                try:
                    kit = Kit.objects.get(uuid=kit_uuid)
                    # Subir la imagen a Supabase Storage
                    image_url, error, storage_path = upload_kit_image_to_supabase(
                        image_file=image_file,
                        kit_uuid=str(kit.uuid)
                    )
                    
                    if error:
                        return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # Actualizar la URL de la imagen en el kit
                    kit.imagen_url = image_url
                    kit.save()
                    
                    return Response({
                        "message": "Imagen subida correctamente",
                        "kit_uuid": str(kit.uuid),
                        "image_url": image_url,
                        "storage_path": storage_path
                    }, status=status.HTTP_200_OK)
                except Kit.DoesNotExist:
                    return Response({"error": "Kit no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Si no se proporciona un kit_uuid, subir la imagen sin asociarla a un kit
                image_url, error, storage_path = upload_kit_image_without_uuid(image_file)
                
                if error:
                    return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                return Response({
                    "message": "Imagen subida correctamente",
                    "image_url": image_url,
                    "storage_path": storage_path
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def upload_image_only(self, request):
        """
        Sube una imagen sin asociarla a ningún kit específico.
        Devuelve la URL de la imagen subida.
        """
        try:
            serializer = KitImageUploadSerializer(data=request.data)
            
            if serializer.is_valid():
                image_file = serializer.validated_data['image']
                
                # Subir la imagen a Supabase Storage
                image_url, error, storage_path = upload_kit_image_without_uuid(image_file)
                
                if error:
                    return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                return Response({
                    "message": "Imagen subida correctamente",
                    "image_url": image_url,
                    "storage_path": storage_path
                }, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KitProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo KitProducto.
    """
    queryset = KitProducto.objects.all()
    serializer_class = KitProductoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return KitProductoCreateUpdateSerializer
        return KitProductoSerializer

    def get_queryset(self):
        queryset = KitProducto.objects.all()
        
        # Filtrar por kit
        kit_uuid = self.request.query_params.get('kit_uuid', None)
        if kit_uuid:
            queryset = queryset.filter(kit__uuid=kit_uuid)
        
        # Ordenar por el campo 'orden'
        queryset = queryset.order_by('orden')
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """
        Actualiza un producto de kit y maneja la imagen del producto si se proporciona.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Obtener la URL de la imagen del producto si existe
        producto_imagen = request.data.get('producto_imagen')
        imagen_url = request.data.get('imagen_url')  # También verificar imagen_url
        
        # Usar producto_imagen o imagen_url, lo que esté disponible
        imagen_final = producto_imagen if producto_imagen else imagen_url
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Si tenemos una URL de imagen, guardarla en la tabla CotizadorImagenproducto
        if imagen_final:
            from .models import CotizadorImagenproducto
            # Guardar la URL tal como viene, sin validación
            imagen_obj, created = CotizadorImagenproducto.objects.update_or_create(
                clave_padre=instance.clave,
                defaults={'url': imagen_final.replace(" ", "%20")}
            )
            print(f"Imagen actualizada para el producto {instance.id}: {imagen_final}")
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # Si '_prefetched_objects_cache' existe, invalidarlo.
            instance._prefetched_objects_cache = {}
            
        # Obtener una instancia fresca del serializer que incluya la imagen actualizada
        response_data = self.get_serializer(instance).data
        
        # Si tenemos una imagen, asegurarnos de que esté en la respuesta
        if imagen_final:
            response_data['producto_imagen'] = imagen_final.replace(" ", "%20")
        
        return Response(response_data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente un producto de kit y maneja la imagen del producto si se proporciona.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class SyncViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    UNIT_PROPERTIES = {
        'osg':{
            'analytic_account_id': 1005
        },
        'gna':{
            'analytic_account_id': 1144
        },
        'sll':{
            'analytic_account_id': 215
        }
    }
    
    def _run_async_task(self, task_function, task_params=None):
        """
        Método auxiliar para ejecutar tareas asíncronas y gestionar sus resultados.
        
        Args:
            task_function: Función a ejecutar de forma asíncrona
            task_params: Parámetros opcionales para la función
            
        Returns:
            Response con información sobre la tarea iniciada
        """
        try:
            import threading
            import uuid
            from datetime import datetime
            
            task_id = f'thread-{uuid.uuid4()}'
            
            def run_task():
                try:
                    # Ejecutar la función con parámetros si se proporcionan
                    if task_params:
                        result = task_function(**task_params)
                    else:
                        result = task_function()
                        
                    # Almacenar los resultados para consulta posterior
                    if not hasattr(SyncViewSet, 'task_results'):
                        SyncViewSet.task_results = {}
                    SyncViewSet.task_results[task_id] = {
                        'task_id': task_id,
                        'status': 'COMPLETED',
                        'timestamp': datetime.now().isoformat(),
                        'stats': result
                    }
                except Exception as e:
                    import traceback
                    if not hasattr(SyncViewSet, 'task_results'):
                        SyncViewSet.task_results = {}
                    SyncViewSet.task_results[task_id] = {
                        'task_id': task_id,
                        'status': 'ERROR',
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                    print(f"Error en tarea asíncrona: {str(e)}")
            
            # Iniciar en un hilo separado
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
            # Devolver respuesta inmediata
            return Response({
                'status': 'success',
                'message': 'Tarea iniciada',
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'check_status_url': f'/api/v1/cotizador/sync/task_status/?task_id={task_id}'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_user_api(self, user):
        print(f"Obteniendo user_api para el usuario: {user}")
        print(f"Tipo de unidad: {user.unidad}")

        try:
            # Intentar obtener el user_api del modelo UserApi
            from apps.accounts.models import Unidad
            unidad = Unidad.objects.filter(user=user).first()
            
            if unidad and unidad.user_api:
                print(f"Usando user_api: {unidad.user_api} como user_id para la consulta de almacenes")
                return unidad.user_api
                
        except Exception as e:
            print(f"Error al obtener user_api: {str(e)}")
            return None

    @action(detail=False, methods=['post'])
    def send_to_hubspot(self, request):

        import requests
        import json
        from django.conf import settings
        
        try:
            # Imprimir la consulta recibida del frontend
            print('=============================================')
            print('CONSULTA RECIBIDA DEL FRONTEND:')
            print(f'Request data: {request.data}')
            print(f'Request headers: {request.headers}')
            print(f'Request method: {request.method}')
            print('=============================================')
            
            # Obtener el UUID de la cotización
            cotizacion_uuid = request.data.get('cotizacion_uuid')
            print(f'UUID de cotización extraído: {cotizacion_uuid}')
            
            # Imprimir el payload completo para depuración
            print('=============================================')
            print('PAYLOAD RECIBIDO DEL FRONTEND (DETALLADO):')
            for key, value in request.data.items():
                print(f'- {key}: {value}')
            print('=============================================')
            
            if not cotizacion_uuid:
                return Response({
                    'status': 'error',
                    'message': 'Se requiere el UUID de la cotización'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener la cotización y sus productos
            cotizacion = get_object_or_404(Cotizacion, uuid=cotizacion_uuid)
            productos = ProductoCotizacion.objects.filter(cotizacion=cotizacion)
            
            # Serializar la cotización y sus productos
            cotizacion_data = CotizacionSerializer(cotizacion).data
            productos_data = ProductoCotizacionSerializer(productos, many=True).data
            
            # Clase para serializar objetos Decimal a float
            class DecimalEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return super(DecimalEncoder, self).default(obj)
            
            # Preparar los datos para enviar al webhook en el formato requerido por HubSpot
            # Obtener el email del vendedor y el subtotal de la cotización
            email_vendedor = cotizacion_data.get('vendedor_info', {}).get('email_vendedor', '')
            subtotal = cotizacion_data.get('operaciones', {}).get('subtotal_mobiliario', 0)
            
            # Convertir la fecha a timestamp en milisegundos para HubSpot
            fecha_proyecto = cotizacion_data.get('fecha_proyecto')
            fecha_timestamp = None
            if fecha_proyecto:
                try:
                    fecha_obj = datetime.strptime(fecha_proyecto, '%Y-%m-%d')
                    fecha_timestamp = int(fecha_obj.timestamp() * 1000)  # Convertir a milisegundos
                except Exception as e:
                    print(f'Error al convertir la fecha: {str(e)}')
            
            # Crear el payload en el formato requerido por HubSpot
            hubspot_payload = {
                'dealname': cotizacion_data.get('proyecto', ''),
                'folio_cotizacion': cotizacion_data.get('folio', ''),
                'email': email_vendedor,
                'total': str(subtotal),
                'date_received': fecha_timestamp
            }
            
            # Enviar solo los datos necesarios para HubSpot
            payload = hubspot_payload
            
            # Convertir el payload a JSON usando el encoder personalizado
            payload_json = json.dumps(payload, cls=DecimalEncoder)
            
            # URL del webhook de n8n desde settings.py
            webhook_url = settings.N8N_WEBHOOK_URL
            
            # Verificar que la URL del webhook esté configurada
            if not webhook_url:
                return Response({
                    'status': 'error',
                    'message': 'La URL del webhook de n8n no está configurada en settings.py'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Enviar los datos al webhook
            try:
                print('Enviando datos al webhook:', webhook_url)
                print('Tamaño del payload:', len(str(payload)))
                
                response = requests.post(
                    webhook_url,
                    data=payload_json,  # Usar el JSON ya serializado en lugar de json=payload
                    headers={'Content-Type': 'application/json'},
                    timeout=10  # Añadir timeout para evitar que se quede esperando indefinidamente
                )
                
                print('Respuesta del webhook - Status code:', response.status_code)
                print('Respuesta del webhook - Contenido COMPLETO:')
                print(response.text)  # Mostrar la respuesta completa
                
                # Intentar parsear la respuesta como JSON
                try:
                    # Verificar si la respuesta tiene contenido
                    if response.text.strip():
                        webhook_response = response.json()
                        print('----------------------------------------')
                        print('Respuesta del webhook como JSON:')
                        print(json.dumps(webhook_response, indent=2))
                        
                        # Obtener el deal_id de la respuesta
                        deal_id = webhook_response.get('dealId')
                        portal_id = webhook_response.get('portalId')
                        
                        if deal_id:
                            print("deal_id:", deal_id)
                            print(f"Link del negocio: https://app.hubspot.com/contacts/{portal_id}/record/0-3/{deal_id}")
                            print('----------------------------------------')
                            
                            # Guardar el deal_id en la cotización
                            cotizacion.hs_deal_id = deal_id
                            cotizacion.save(update_fields=['hs_deal_id'])
                            print(f"Se guardó el deal_id {deal_id} en la cotización {cotizacion.folio}")
                        else:
                            print("No se encontró deal_id en la respuesta")
                    else:
                        print("La respuesta del webhook está vacía")
                        print("Es posible que el webhook no esté activo o que necesites hacer clic en 'Test workflow' en n8n")
                except Exception as e:
                    print('La respuesta no es un JSON válido:', str(e))
                    print('Contenido de la respuesta:', response.text[:100], '...' if len(response.text) > 100 else '')
            except requests.exceptions.Timeout as e:
                print('Error de timeout al enviar datos al webhook:', str(e))
                return Response({
                    'status': 'error',
                    'message': 'Timeout al enviar datos al webhook',
                    'error': str(e)
                }, status=status.HTTP_504_GATEWAY_TIMEOUT)
            except requests.exceptions.RequestException as e:
                print('Error al enviar datos al webhook:', str(e))
                return Response({
                    'status': 'error',
                    'message': 'Error al enviar datos al webhook',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verificar la respuesta
            if response.status_code >= 200 and response.status_code < 300:
                return Response({
                    'status': 'success',
                    'message': 'Datos enviados correctamente a HubSpot',
                    'webhook_response': response.json() if response.text else {},
                    'hubspot_data': payload  # Incluir los datos enviados a HubSpot
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Error al enviar datos al webhook: {response.text}',
                    'status_code': response.status_code
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            import traceback
            return Response({
                'status': 'error',
                'message': f'Error al procesar la solicitud: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sync_products(self, request):
        """
        Endpoint para activar manualmente la sincronización de productos.
        Puede ser llamado desde n8n u otras herramientas de automatización.
        """
        from .cache.sync import sync_products_to_supabase
        return self._run_async_task(sync_products_to_supabase)
    
    @action(detail=False, methods=['post'])
    def sync_products_manual(self, request):
        """
        Endpoint POST para activar manualmente la sincronización de productos.
        Diseñado para ser llamado desde una interfaz de usuario o API.
        Permite verificar que la sincronización esté correctamente configurada.
        """
        from .cache.sync import sync_products_to_supabase
        return self._run_async_task(sync_products_to_supabase)

    @action(detail=False, methods=['post'])
    def sync_images(self, request):
        """
        Endpoint POST para activar manualmente la sincronización de imágenes de productos.
        Sincroniza las URLs de imágenes desde la tabla cotizador_imagenproducto a products_cache.
        NOTA: Este proceso puede tardar varios minutos en completarse.
        """
        from django.core.management import call_command
        
        # Parámetros opcionales de la solicitud
        batch_size = request.data.get('batch_size', 100)
        validate_urls = request.data.get('validate_urls', False)
        force_update = request.data.get('force_update', False)
        
        def sync_images_task():
            from io import StringIO
            import sys
            import time
            
            # Registrar tiempo de inicio
            start_time = time.time()
            
            # Capturar la salida del comando
            output = StringIO()
            original_stdout = sys.stdout
            sys.stdout = output
            
            # Ejecutar el comando de sincronización
            call_command(
                'sync_products_cache_images',
                batch_size=batch_size,
                validate_urls=validate_urls,
                force_update=force_update,
                verbosity=2
            )
            
            # Restaurar stdout
            sys.stdout = original_stdout
            
            # Calcular tiempo total de ejecución
            execution_time = time.time() - start_time
            
            # Procesar la salida para extraer estadísticas
            output_text = output.getvalue()
            lines = output_text.split('\n')
            
            # Extraer estadísticas
            stats = {}
            for line in lines:
                if 'Total de productos procesados:' in line:
                    stats['total_productos'] = int(line.split(':')[1].strip())
                elif 'Productos actualizados:' in line:
                    stats['actualizados'] = int(line.split(':')[1].strip())
                elif 'Productos sin cambios:' in line:
                    stats['sin_cambios'] = int(line.split(':')[1].strip())
                elif 'Productos sin imagen:' in line:
                    stats['sin_imagen'] = int(line.split(':')[1].strip())
                elif 'Errores:' in line and 'Error' not in line[:5]:  # Evitar líneas de error completas
                    stats['errores'] = int(line.split(':')[1].strip())
            
            # Añadir detalles adicionales
            stats['execution_time_seconds'] = round(execution_time, 2)
            stats['details'] = output_text[-2000:] if len(output_text) > 2000 else output_text
            
            return stats
        
        return self._run_async_task(sync_images_task)
    
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """
        Endpoint para consultar el estado de una tarea asíncrona.
        """
        task_id = request.query_params.get('task_id')
        
        if not task_id:
            return Response({
                'status': 'error',
                'message': 'Se requiere el parámetro task_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verificar si tenemos resultados para esta tarea
        if hasattr(SyncViewSet, 'task_results') and task_id in SyncViewSet.task_results:
            return Response(SyncViewSet.task_results[task_id])
        elif task_id.startswith('thread-'):
            response_data = {
                'task_id': task_id,
                'status': 'RUNNING',
            }
            return Response(response_data)
        else:
            return Response({
                'status': 'error',
                'message': f'No se encontró la tarea con ID: {task_id}'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def sync_products_async(self, request):
        """
        Endpoint para activar la sincronización de productos como tarea asíncrona.
        Inicia la tarea pero no espera a que termine.
        """
        from .cache.sync import sync_products_to_supabase
        return self._run_async_task(sync_products_to_supabase)
    
    @action(detail=False, methods=['get'])
    def get_clients(self, request):
        """
        Endpoint para obtener todos los clientes desde Supabase.
        """
        try:
            # Obtener los clientes desde Supabase
            clients = get_clients_from_supabase()
            
            # Devolver los clientes
            return Response({
                'status': 'success',
                'count': len(clients),
                'clients': clients
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error en get_clients: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_wearehouses(self, request):
        try:
            import json
            import requests
            
            user = request.user
            user_api = self.get_user_api(user)
            if not user_api:
                return Response({
                    'status': 'error',
                    'message': 'El usuario no tiene un usuario API'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            print(f"Consultando almacenes con user_api: {user_api}")
            url = f"https://api2.ercules.mx/api/v1/common/location_classifications?user_id={user_api}&classification=0&names=0"
            print(f"URL de consulta: {url}")
            
            response = requests.get(url)
            
            # Obtener todos los datos para depuraciu00f3n
            all_data = response.json()
            
            # Filtrar solo los almacenes
            warehouses = []
            for item in all_data:
                if item.get('classification') == 'warehouse':
                    if user_api == '881':
                        wherehouse_code = item.get('code')
                        if 'PUE' == wherehouse_code or 'GDL' == wherehouse_code or 'QRO' == wherehouse_code:
                            print(f"Almacen encontrado para usuario {user_api}: {item.get('name')}")
                            if wherehouse_code == 'QRO':
                                item['name'] = 'Querétaro'
                            warehouses.append(item)
                        else:
                            print(f"Almacen no encontrado para usuario {user_api}: {item.get('name')}")
            print(f"Se han encontrado {len(warehouses)} almacenes")
            print(json.dumps(warehouses, indent=4))
            
            # Devolver la respuesta con todos los datos para depuraciu00f3n
            return Response({
                'status': 'success',
                'count': len(warehouses),
                'warehouses': warehouses,
                'all_locations': all_data  # Incluir todos los datos para depuraciu00f3n
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error en get_wearehouses: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        print("=== INICIO CREATE_ORDER ===")
        print("Datos recibidos:", request.data)

        """
        Endpoint para crear una orden de venta en Odoo.
        
        Recibe los datos de la cotizaciu00f3n desde el frontend y crea una orden de venta en Odoo.
        
        Ejemplo de payload:
        {
            "partner_id": 10242,
            "client_order_ref": "Referencia del cliente",
            "priority": "replenishment",
            "manufacture": "replenishment",
            "warehouse_id": 1,
            "fiscal_position_id": 3,
            "analytic_account_id": 1,
            "hubspot_id": 3336452,

            "products": [
                {
                    "product_id": 1683294,
                    "product_uom_qty": 2,
                    "price_unit": 9000,
                    "route_id": 55
                },
                {
                    "product_id": 1683294,
                    "product_uom_qty": 1,
                    "price_unit": 9000,
                    "route_id": 55
                }
            ]
        }
        """
        # Importar los módulos necesarios al inicio de la función
        import json
        from decimal import Decimal
        from datetime import datetime
        import requests
        try:
            from decouple import config
            
            # Obtener el endpoint de Odoo
            odoo_endpoint = config('ODOO_ENDPOINT')            
            # Verificar si el endpoint incluye el modelo y la acciu00f3n
            if 'model=' not in odoo_endpoint and 'action=' not in odoo_endpoint:
                # Si no estu00e1n incluidos, agregar los paru00e1metros necesarios
                odoo_endpoint = f"{odoo_endpoint}?model=sale.order&action=create_order"
            
            # Clase para serializar Decimal a float
            class DecimalEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return super(DecimalEncoder, self).default(obj)

            # Normalizar el nombre de la unidad (quitar acentos y convertir a minsculas)
            import unicodedata
            def normalize_string(s):
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
            
            unit_name = normalize_string(request.user.unidad.nombre_corto)
            # Registro mínimo para depuración
            
            # Obtener las claves API directamente usando config()
            from decouple import config
            
            try:
                if unit_name == 'cdmx':
                    api_key = config('user_pass_cdmx')
                    password = config('pass_cdmx')
                elif unit_name == 'laguna':
                    api_key = config('user_pass_laguna')
                    password = config('pass_laguna')
                elif unit_name == 'monterrey':
                    api_key = config('user_pass_mty')
                    password = config('pass_mty')
                elif unit_name in ['puebla', 'queretaro', 'guadalajara']:
                    api_key = config('user_pass_pue_qro_gdl')
                    password = config('pass_pue_qro_gdl')
                else:
                    # Si no coincide con ninguna unidad conocida, usar la API key predeterminada
                    api_key = config('ODOO_API_KEY')
                    password = config('ODOO_PASSWORD', '')
                
            except Exception as e:
                print(f"Error al obtener la clave API: {str(e)}")
                return Response({'status': 'error', 'message': 'Error al obtener la clave API', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            serializer = CreateOrderSerializer(data=request.data)
            if not serializer.is_valid():
                # Error de validación - mostrar errores detallados
                print(f"Error de validación: {serializer.errors}")

                # Crear mensajes de error más descriptivos
                error_messages = {}
                error_detail = ""

                for field, errors in serializer.errors.items():
                    if field == 'client_order_ref':
                        error_messages[field] = ['El campo Folio de Cotización es obligatorio. Por favor, complételo.']
                        error_detail += "El campo Folio de Cotización es obligatorio. "
                    else:
                        error_messages[field] = errors
                        # Convertir todos los elementos de la lista de errores a strings antes de unirlos
                        error_strings = [str(error) for error in errors]
                        error_detail += f"El campo {field} tiene errores: {', '.join(error_strings)}. "
                
                return Response({
                    'status': 'error',
                    'message': f'Error al crear el presupuesto {error_detail.strip()}',
                    'errors': error_messages,
                    'detail': error_detail.strip()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data.copy()
            print(f"DATOS RECIBIDOS DEL FRONTEND: {json.dumps(validated_data, indent=4, cls=DecimalEncoder)}")
            
            try:
                razon_social = request.data.get('razon_social', '').lower()
                if razon_social:
                    razon_key = razon_social.lower()
                    if razon_key in ['osg', 'operadora de sucursales gebesa']:
                        razon_key = 'osg'
                    elif razon_key in ['gna', 'gebesa nacional']:
                        razon_key = 'gna'
                    elif razon_key in ['sll', 'sistemas de logistu00edca laboral']:
                        razon_key = 'sll'
                    if razon_key in self.UNIT_PROPERTIES:
                        unit_properties = self.UNIT_PROPERTIES[razon_key]
                        for key, value in unit_properties.items():
                            validated_data[key] = value
                    else:
                        print(f"No se encontraron propiedades para la razu00f3n social: {razon_key}")
                        # Asignar None (null) al campo analytic_account_id
                        validated_data['analytic_account_id'] = None
                else:
                    unit_name = normalize_string(request.user.unidad.nombre_corto)
                    if unit_name in self.UNIT_PROPERTIES:
                        unit_properties = self.UNIT_PROPERTIES[unit_name]
                        for key, value in unit_properties.items():
                            validated_data[key] = value
                    else:
                        print(f"No se encontraron propiedades para la unidad: {unit_name}")
                        # Asignar None (null) al campo analytic_account_id
                        validated_data['analytic_account_id'] = None
                        
            except Exception as e:
                print(f"Error al aplicar propiedades de unidad: {str(e)}")
            
            # Agregar el hubspot_id si existe en la cotización
            if 'uuid' in request.data:
                validated_data['uuid'] = request.data['uuid']
                try:
                    cotizacion = Cotizacion.objects.get(uuid=request.data['uuid'])
                    if cotizacion.hs_deal_id:
                        validated_data['hubspot_id'] = cotizacion.hs_deal_id
                        print(f"Agregando hubspot_id: {cotizacion.hs_deal_id}")
                except Exception as e:
                    print(f"Error al obtener el hubspot_id de la cotización: {str(e)}")
            
            odoo_data = serializer.to_odoo_format(validated_data)
            print(f"ODOO DATA: {json.dumps(odoo_data, indent=4, cls=DecimalEncoder)}")

            
            # Obtener el vendedor_id del usuario actual si está disponible
            vendedor_id = request.data.get('vendedor_id')
            if not vendedor_id:
                print(f"No se encontró vendedor_id en el payload")
                vendedor_id = None
            if not vendedor_id and hasattr(request.user, 'vendedor_id') and request.user.vendedor_id:
                try:
                    vendedor_id = int(request.user.vendedor_id)
                    print(f"Usando vendedor_id del usuario: {vendedor_id}")
                except (ValueError, TypeError) as e:
                    print(f"Error al convertir vendedor_id a entero: {e}")
            
            # Si no se pudo obtener el vendedor_id del usuario, usar el que viene en los datos
            if not vendedor_id and 'user_id' in odoo_data:
                vendedor_id = odoo_data['user_id']
                print(f"Usando user_id de odoo_data: {vendedor_id}")

            if vendedor_id is not None:
                odoo_data['user_id'] = vendedor_id
                print(f"Usando vendedor_id FINAL: {vendedor_id}")
            
            # Preparar el payload final para Odoo
            payload = {
                "fields": ["name", "partner_id", "client_order_ref", "priority", "order_line", "manufacture", "warehouse_id", "note", "user_id"],
                "values": odoo_data
            }
            

            
            try:
                payload_json = json.dumps(payload, cls=DecimalEncoder)
                # Un solo log con la información esencial para depuración
                print('\nPAYLOAD PREPARADO PARA ODOO')
                print(payload_json)
            except Exception as e:
                print(f"Error al preparar los datos para Odoo: {str(e)}")
                return Response({'status': 'error', 'message': 'Error al preparar los datos para Odoo', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Configurar los headers exactamente como se muestra en Postman
            headers = {
                'Content-Type': 'application/json',
                'login': request.user.unidad.odoo_user.email,
                'password': password,
                'Api-Key': api_key
            }

            # No mostrar headers completos para proteger información sensible
            print("Headers preparados para la petición a Odoo")
            
            # Realizar una simple petición POST a la API de Odoo
            response = requests.post(odoo_endpoint, data=payload_json, headers=headers)
            
            # Verificar si la petición fue exitosa
            response.raise_for_status()
        
            # Procesar la respuesta de Odoo
            odoo_response = response.json()
            
            try:
                # La respuesta de Odoo viene en un formato anidado y escapado
                if odoo_response.get('result') and isinstance(odoo_response['result'], list):
                    #Parsear el string JSON que viene dentro del primer elemento
                    inner_result = json.loads(odoo_response['result'][0])
                    if 'New resource' in inner_result and isinstance(inner_result['New resource'], list):
                        order_data = inner_result['New resource'][0]

                        # Log simplificado de la operación exitosa
                        print("Orden creada exitosamente en Odoo")


                        # Actualizar el folio de la cotización
                        try:
                            #Obtener el uuid de la cotizacion
                            cotizacion_uuid = request.data.get('uuid')
                            print(f"UUID de la cotización: {cotizacion_uuid}")
                            if cotizacion_uuid:
                                #Obtener la cotizacion
                                cotizacion = Cotizacion.objects.get(uuid=cotizacion_uuid)
                                cotizacion.odoo_so = order_data.get('name')
                                cotizacion.estatus = 'enviado'
                                cotizacion.save()
                                print(f"Cotización actualizada con el folio de Odoo: {order_data.get('name')}")

                        except Exception as e:
                            print(f"Error al actualizar el folio de la cotización: {str(e)}")

                        #Construir una respuesta limpia y estructurada
                        formatted_response = {
                            'status': 'success',
                            'message': 'Orden creada exitosamente',
                            'order': {
                                'id': order_data.get('id'),
                                'so': order_data.get('name'),
                                'client_order_ref': order_data.get('client_order_ref'),
                                'priority': order_data.get('priority'),
                                'manufacture': order_data.get('manufacture'),
                                'warehouse_id': order_data.get('warehouse_id'),
                                'fiscal_position_id': order_data.get('fiscal_position_id'),
                                'analytic_account_id': order_data.get('analytic_account_id'),
                                'hubspot_id': order_data.get('hubspot_id'),
                                'partner': {
                                    'id': order_data.get('partner_id')[0] if isinstance(order_data.get('partner_id'), list) else None,
                                    'name': order_data.get('partner_id')[1] if isinstance(order_data.get('partner_id'), list) and len(order_data.get('partner_id')) > 1 else None
                                },
                                'order_line': order_data.get('order_line', [])
                            }
                        }

                        print("\n===== RESPUESTA DEL ENDPOINT =====")
                        print(json.dumps(formatted_response, indent=4, ensure_ascii=False))
                        print("===================================\n")

                        # Devolver la respuesta
                        return Response(formatted_response, status=status.HTTP_201_CREATED)
                        
                else:
                    formatted_response = {
                        'status': 'error',
                        'message': 'No se pudo crear la orden de venta',
                        'data': odoo_response
                    }
                    return Response(formatted_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            except Exception as e:
                # Si hay algún error al formatear, devolvemos la respuesta original
                print(f"Error al formatear la respuesta: {str(e)}")
                formatted_response = {
                    'status': 'error',
                    'message': f'Error al procesar la respuesta: {str(e)}',
                    'data': odoo_response
                }
                return Response(formatted_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Si hay algún error en la petición a Odoo
            print(f"\n===== ERROR EN CREATE_ORDER =====")
            print(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Error al crear la orden en Odoo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def sync_clients(self, request):
        """
        Endpoint para sincronizar clientes desde la API de Hércules a Supabase.
        Ejecuta la sincronización de forma síncrona y devuelve los resultados.
        """
        try:
            # Obtener parámetros de la solicitud con valores predeterminados
            params = {
                'user_id': request.data.get('user_id', 1),
                'fecha_ini': request.data.get('fecha_ini', '2009-09-01'),
                'fecha_fin': request.data.get('fecha_fin', '2025-09-04'),
                'name': request.data.get('name', 'gebesa')
            }
            
            from .cache.sync import sync_clients_to_supabase
            import requests
            from datetime import datetime
            
            start_time = datetime.now()
            
            # Construir la URL con los parámetros
            api_url = "https://api.ercules.mx/api/v1/common/res_partner"
            
            # Realizar la petición a la API
            print(f"Consultando API: {api_url}")
            response = requests.get(api_url, params=params)
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                raise Exception(f"Error al consultar la API: {response.status_code}")
            
            # Convertir la respuesta a JSON
            clients_data = response.json()
            
            if not clients_data:
                print("No se encontraron clientes en la API")
                return Response({
                    'status': 'success',
                    'message': 'No se encontraron clientes en la API',
                    'stats': {
                        'total': 0,
                        'successful': 0,
                        'errors': 0,
                        'duration': "0:00:00"
                    }
                }, status=status.HTTP_200_OK)
            
            print(f"Se encontraron {len(clients_data)} clientes en la API")
            
            # Sincronizar con Supabase
            stats = sync_clients_to_supabase(clients_data)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Devolver resultados
            return Response({
                'status': 'success',
                'message': f"Se sincronizaron {stats['successful']} de {stats['total']} clientes",
                'stats': stats,
                'duration': str(duration),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error en sincronización de clientes: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Error en la sincronización de clientes: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='external-clients')
    def get_external_clients(self, request):
        import json

        try:
            # Obtener parámetros de la solicitud con valores predeterminados
            user_id = request.query_params.get('user_id', '1')
            unidad = request.query_params.get('unidad', '0')
            
            # Si user_id es 'undefined', usar el valor por defecto '1'
            if user_id == 'undefined' or not user_id:
                user_id = '1'
            
            # Verificar si el usuario actual tiene user_api definido en su unidad
            user_api = None
            try:
                if hasattr(request.user, 'unidad') and request.user.unidad and hasattr(request.user.unidad, 'user_api'):
                    user_api = request.user.unidad.user_api
                    if user_api:
                        # Si tiene user_api, usarlo como user_id y no usar name
                        user_id = user_api
                        name_param = '0'  # No usar filtro de nombre cuando se tiene user_api
                        print(f"Usando user_api: {user_api} como user_id para la consulta de clientes")
            except Exception as e:
                print(f"Error al obtener user_api: {str(e)}")
                # Continuar con el flujo normal si hay error
            
            # Si no se usó user_api, proceder con la lógica original
            if not user_api:
                # Si no tiene user_api, devolver lista vacía sin consultar la API
                print(f"Usuario {request.user.username} no tiene user_api configurado. No se consultará la API.")
                debug_info = {
                    'tiene_unidad': hasattr(request.user, 'unidad') and request.user.unidad is not None,
                    'unidad_nombre': getattr(request.user.unidad, 'nombre', 'No disponible') if hasattr(request.user, 'unidad') and request.user.unidad else 'No tiene unidad',
                    'username': request.user.username,
                    'error': 'No tiene user_api configurado'
                }
                print(f"Usuario {request.user.username} no tiene user_api configurado. No se consultará la API.")
                print(f"Debug info: {debug_info}")
                # Devolvemos un array vacío para mantener compatibilidad con el frontend
                return Response([], status=status.HTTP_200_OK)
            
            params = {
                'user_id': user_id,
                'fecha_ini': request.query_params.get('fecha_ini', '2009-09-01'),
                'fecha_fin': request.query_params.get('fecha_fin', '2025-09-04'),
                'name': request.query_params.get('name', '0')
            }

            from urllib.parse import urlencode
            print(f"Parámetros recibidos: {request.query_params}")
            print(f"Parámetros enviados a la API: {params}")
            print(f"URL completa: https://api.ercules.mx/api/v1/common/res_partner?{urlencode(params)}")

            import requests
            
            # Construir la URL con los parámetros
            api_url = "https://api.ercules.mx/api/v1/common/res_partner"
            
            # Realizar la petición a la API
            response = requests.get(api_url, params=params)

            print(f"Respuesta de la API: {json.dumps(response.json(), indent=4)}")
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                return Response({
                    'status': 'error',
                    'message': f'Error al consultar la API: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener los datos de la respuesta
            clients_data = response.json()
            
            # Filtrar y formatear los datos como se hace en el frontend
            formatted_clients = []
            client_map = {}
            
            for client in clients_data:
                # Excluir clientes con @ en su nombre
                if '@' in client.get('name_partner', ''):
                    continue
                    
                partner_id = client.get('partner_id')
                if partner_id and partner_id not in client_map:
                    client_map[partner_id] = {
                        'partner_id': partner_id,
                        'name_partner': client.get('name_partner', ''),
                        'rfc': client.get('rfc', ''),
                        'direccion': client.get('direccion', ''),
                        'ciudad': client.get('ciudad', ''),
                        'estado': client.get('estado', ''),
                        'original_data': client
                    }
            
            # Convertir el diccionario a lista
            formatted_clients = list(client_map.values())
            
            return Response(formatted_clients, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error al obtener clientes externos: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Error al obtener clientes externos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='validate-product')
    def validate_product(self, request):
        """
        Endpoint para validar productos especiales consultando la API de Ercules.
        Actúa como proxy para evitar problemas de CORS en el frontend.
        
        Parámetros de consulta:
        - user_id: ID del usuario (default: 2)
        - products: Códigos de productos separados por comas
        - product_tmpl_ids: IDs de plantillas de producto (default: 0)
        - line_ids: IDs de líneas (default: 0)
        - group_ids: IDs de grupos (default: 0)
        - type_ids: IDs de tipos (default: 0)
        - family_ids: IDs de familias (default: 0)
        - only_line: Bandera para filtrar solo por línea (default: 0)
        """
        try:
            
            # Obtener parámetros de la solicitud con valores predeterminados
            params = {
                'user_id': request.query_params.get('user_id', '2'),
                'products': request.query_params.get('products', ''),
                'product_tmpl_ids': request.query_params.get('product_tmpl_ids', '0'),
                'line_ids': request.query_params.get('line_ids', '0'),
                'group_ids': request.query_params.get('group_ids', '0'),
                'type_ids': request.query_params.get('type_ids', '0'),
                'family_ids': request.query_params.get('family_ids', '0'),
                'only_line': request.query_params.get('only_line', '0')
            }
             
            import requests
            
            # Construir la URL con los parámetros
            api_url = "https://api2.ercules.mx/api/v1/common/product_data"
            
            # Realizar la petición a la API
            response = requests.get(api_url, params=params)
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                return Response({
                    'status': 'error',
                    'message': f'Error al consultar la API: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener los datos de la respuesta
            product_data = response.json()
            
            return Response(product_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error al validar producto: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Error al validar producto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    