from django.db import models
from django.utils import timezone
from apps.accounts.models import User, UserProfile

class Categoria(models.Model):
    """
    Modelo para gestionar las categorías de productos disponibles
    """
    categoria_id = models.IntegerField(
        primary_key=True,
        help_text='ID de la categoría de productos'
    )
    nombre = models.CharField(
        max_length=100,
        help_text='Nombre descriptivo de la categoría'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción detallada de la categoría'
    )
    activo = models.BooleanField(
        default=True,
        help_text='Indica si la categoría está activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.categoria_id})"

import requests
from rest_framework import status

class Almacen:
    """
    Clase proxy para interactuar con la API externa de Odoo que proporciona la información de almacenes.
    Esta clase NO almacena datos localmente, sino que sirve como interfaz para la API externa.
    Todos los datos son consultados en tiempo real a la API externa cada vez que se necesitan.
    """
    API_URL = 'https://api2.ercules.mx/api/v1/common/location_classifications'
    
    @classmethod
    def obtener_parametros_api(cls):
        """
        Devuelve los parámetros comunes para las solicitudes a la API externa
        """
        return {
            'user_id': 2,  # ID del usuario para la API externa
            'classification': 0,
            'names': 0
        }
    
    @classmethod
    def obtener_almacenes(cls, filtros=None):
        """
        Obtiene la lista de almacenes directamente desde la API externa
        
        Args:
            filtros (dict, opcional): Filtros adicionales para la consulta
            
        Returns:
            dict: Respuesta de la API externa con los almacenes
        """
        try:
            params = cls.obtener_parametros_api()
            
            # Agregar filtros adicionales si se proporcionan
            if filtros and isinstance(filtros, dict):
                params.update(filtros)
                
            response = requests.get(cls.API_URL, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': True,
                    'message': f'Error en la API externa: {response.status_code}',
                    'status_code': response.status_code
                }
        except Exception as e:
            return {
                'error': True,
                'message': f'Error al consultar la API externa: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    @classmethod
    def obtener_almacen_por_id(cls, almacen_id):
        """
        Obtiene un almacén específico por su ID
        
        Args:
            almacen_id: ID del almacén a consultar
            
        Returns:
            dict: Datos del almacén o error si no se encuentra
        """
        try:
            # Obtener todos los almacenes y filtrar por ID
            almacenes_data = cls.obtener_almacenes()
            
            if 'error' in almacenes_data:
                return almacenes_data
                
            for item in almacenes_data.get('data', []):
                if str(item.get('id')) == str(almacen_id):
                    return item
                    
            return {
                'error': True,
                'message': f'Almacén con ID {almacen_id} no encontrado',
                'status_code': status.HTTP_404_NOT_FOUND
            }
        except Exception as e:
            return {
                'error': True,
                'message': f'Error al consultar la API externa: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }

class PropuestaCompra(models.Model):
    """
    Modelo para gestionar propuestas de compra basadas en el pronóstico de existencias
    """
    ESTADO_BORRADOR = 'borrador'
    ESTADO_PENDIENTE_APROBACION = 'pendiente_aprobacion'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_MODIFICADA_APROBADA = 'modificada_aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_ENVIADA = 'enviada'
    ESTADO_REGISTRADA_ODOO = 'registrada_odoo' # Nuevo estado
    
    ESTADOS_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_PENDIENTE_APROBACION, 'Pendiente Aprobación'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_MODIFICADA_APROBADA, 'Modificada y Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
        (ESTADO_ENVIADA, 'Enviada a Proveedor'),
        (ESTADO_REGISTRADA_ODOO, 'Registrada en Odoo'), # Nuevo choice
    ]
    
    # Relaciones
    comprador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='propuestas_compra',
        help_text='Usuario comprador que genera la propuesta'
    )
    # Ya no almacenamos IDs de almacenes pues no tiene sentido en este contexto
    
    # Campos básicos
    numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Número o identificador de la propuesta'
    )
    estado = models.CharField(
        max_length=25,
        choices=ESTADOS_CHOICES,
        default=ESTADO_BORRADOR,
        help_text='Estado actual de la propuesta de compra'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha de última actualización'
    )
    fecha_envio = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de envío de la propuesta'
    )
    fecha_aprobacion_rechazo = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de aprobación o rechazo de la propuesta'
    )
    
    # Campos adicionales
    historial_eventos = models.JSONField(
        default=list,
        blank=True,
        help_text='Historial de eventos y comentarios de la propuesta'
    )
    usuario_aprobador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='propuestas_aprobadas',
        help_text='Usuario que aprobó o rechazó la propuesta'
    )
    proveedor = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Proveedor principal asociado a esta propuesta'
    )
    
    # New fields for Almacen and Categoria context
    almacenes_ids = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text='Lista de IDs y nombres de almacenes seleccionados para la propuesta (ej: [{"id": 1, "name": "Almacen A"}])'
    )
    categoria_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text='ID de la categoría seleccionada para la propuesta'
    )
    categoria_nombre = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text='Nombre de la categoría seleccionada para la propuesta'
    )
    fecha_registro_odoo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Registro en Odoo",
        help_text='Fecha y hora en que la propuesta fue registrada en Odoo'
    )
    odoo_purchase_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="ID de Orden de Compra en Odoo",
        help_text='ID o referencia de la Orden de Compra generada en Odoo'
    )
    
    odoo_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Respuesta de Odoo",
        help_text='Respuesta completa de Odoo al crear la orden de compra'
    )

    # Items de la propuesta
    # related_name='items' se define en el ForeignKey de ItemPropuestaCompra
    class Meta:
        verbose_name = 'Propuesta de Compra'
        verbose_name_plural = 'Propuestas de Compra'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Propuesta {self.id or ''} por {self.comprador.username} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        # Aquí podríamos añadir lógica adicional si fuera necesario antes de guardar
        super().save(*args, **kwargs)

    # Renamed from enviar
    def solicitar_aprobacion(self):
        """Cambia el estado de la propuesta a pendiente de aprobación y registra el evento."""
        if self.estado == self.ESTADO_BORRADOR:
            estado_anterior = self.estado
            self.estado = self.ESTADO_PENDIENTE_APROBACION
            self.fecha_envio = timezone.now()

            evento = {
                "timestamp": timezone.now().isoformat(),
                "usuario_id": self.comprador.id,
                "usuario_nombre": self.comprador.get_full_name() or self.comprador.username,
                "accion": f"{estado_anterior} -> {self.estado}",
                "tipo_accion": "solicitud_aprobacion",
                "comentario": "Propuesta enviada para aprobación."
            }
            if not isinstance(self.historial_eventos, list):
                self.historial_eventos = []
            self.historial_eventos.append(evento)
            self.save()
            return True
        return False

    def aprobar(self, usuario, comentarios=None):
        """Aprueba la propuesta, elimina items sin cantidad propuesta y registra el evento."""
        if self.estado == self.ESTADO_PENDIENTE_APROBACION:
            estado_anterior = self.estado
            # Eliminar items sin propuesta (cantidad_propuesta = 0)
            self.items.filter(cantidad_propuesta=0).delete()
            
            # Actualizar el estado de la propuesta
            self.estado = self.ESTADO_APROBADA
            self.fecha_aprobacion_rechazo = timezone.now()
            self.usuario_aprobador = usuario

            evento = {
                "timestamp": timezone.now().isoformat(),
                "usuario_id": usuario.id,
                "usuario_nombre": usuario.get_full_name() or usuario.username,
                "accion": f"{estado_anterior} -> {self.estado}",
                "tipo_accion": "aprobacion",
                "comentario": comentarios if comentarios else "Propuesta aprobada."
            }
            if not isinstance(self.historial_eventos, list):
                self.historial_eventos = []
            self.historial_eventos.append(evento)
            self.save()
            return True
        return False

    def rechazar(self, usuario, comentarios=None):
        """Rechaza la propuesta y registra el evento."""
        # Permitir rechazar si está pendiente de aprobación, aprobada, o modificada y aprobada
        if self.estado in [self.ESTADO_PENDIENTE_APROBACION, self.ESTADO_APROBADA, self.ESTADO_MODIFICADA_APROBADA]:
            estado_anterior = self.estado
            self.estado = self.ESTADO_RECHAZADA
            self.fecha_aprobacion_rechazo = timezone.now()
            self.usuario_aprobador = usuario

            evento = {
                "timestamp": timezone.now().isoformat(),
                "usuario_id": usuario.id,
                "usuario_nombre": usuario.get_full_name() or usuario.username,
                "accion": f"{estado_anterior} -> {self.estado}",
                "tipo_accion": "rechazo",
                "comentario": comentarios if comentarios else "Propuesta rechazada."
            }
            if not isinstance(self.historial_eventos, list):
                self.historial_eventos = []
            self.historial_eventos.append(evento)
            self.save()
            return True
        return False

    # New method to mark as sent to supplier
    def enviar_proveedor(self, usuario_envia=None): # Permitir pasar el usuario que envía
        """Marca la propuesta como enviada al proveedor y registra el evento."""
        if self.estado in [self.ESTADO_APROBADA, self.ESTADO_MODIFICADA_APROBADA]:
            estado_anterior = self.estado
            self.estado = self.ESTADO_ENVIADA
            
            usuario_id_evento = usuario_envia.id if usuario_envia else self.comprador.id
            usuario_nombre_evento = (usuario_envia.get_full_name() or usuario_envia.username) if usuario_envia else (self.comprador.get_full_name() or self.comprador.username)

            evento = {
                "timestamp": timezone.now().isoformat(),
                "usuario_id": usuario_id_evento,
                "usuario_nombre": usuario_nombre_evento,
                "accion": f"{estado_anterior} -> {self.estado}",
                "tipo_accion": "envio_proveedor",
                "comentario": "Propuesta marcada como enviada al proveedor."
            }
            if not isinstance(self.historial_eventos, list):
                self.historial_eventos = []
            self.historial_eventos.append(evento)
            # Potentially add fecha_envio_proveedor field?
            self.save()
            return True
        return False

class ItemPropuestaCompra(models.Model):
    """
    Modelo para representar cada item de producto en una propuesta de compra
    """
    propuesta = models.ForeignKey(
        PropuestaCompra,
        on_delete=models.CASCADE,
        related_name='items',  
        help_text='Propuesta de compra a la que pertenece este item'
    )
    
    # Información del producto
    categoria = models.CharField(
        max_length=100,
        help_text='Categoría del producto'
    )
    codigo = models.CharField(
        max_length=50,
        help_text='Código del producto'
    )
    producto = models.CharField(
        max_length=255,
        help_text='Nombre del producto'
    )
    medida = models.CharField(
        max_length=20,
        help_text='Unidad de medida del producto'
    )
    
    # Campos del Pronóstico de Existencias
    costo = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Costo unitario del producto según pronóstico'
    )
    existencia = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Existencia actual según pronóstico'
    )
    comprometido = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Cantidad comprometida según pronóstico'
    )
    libre = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Cantidad libre (Existencia - Comprometido) según pronóstico'
    )
    consumo_mensual = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Consumo mensual promedio según pronóstico'
    )
    inv_mensuales = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=0.0,
        help_text='Meses de inventario según pronóstico'
    )
    
    # Cantidades de existencias y propuesta
    cantidad_oc = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=0,
        help_text='Cantidad en órdenes de compra abiertas según pronóstico'
    )
    registrar = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=0,
        help_text='Ya en planta pero no se ha registrado'
    )
    produccion = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=0,
        help_text='No está en planta pero ya está pedido'
    )
    cantidad_propuesta = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text='Cantidad propuesta para compra'
    )
    
    # Información adicional
    meses = models.DecimalField(
        max_digits=12, 
        decimal_places=6,
        help_text='Meses de cobertura (Libre + Por Registrar + En producción + Propuesta / Consumo Mensual)'
    )
    comentarios = models.TextField(
        blank=True,
        null=True,
        help_text='Comentarios adicionales sobre este item'
    )
    proveedor_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID del proveedor asignado a este item'
    )
    product_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID del producto en Odoo'
    )
    medida_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID de la unidad de medida en Odoo'
    )
    currency_id = models.IntegerField(
        null=True,
        blank=True,
        default=3,  # Default: MXN (Pesos Mexicanos)
        help_text='ID de la moneda en Odoo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Item de Propuesta de Compra'
        verbose_name_plural = 'Items de Propuesta de Compra'
        ordering = ['propuesta', 'codigo']
        unique_together = [['propuesta', 'codigo']]  
        db_table = 'compras_itempropuestacompra'  
    
    def __str__(self):
        return f"{self.codigo} - {self.producto} ({self.propuesta})"
