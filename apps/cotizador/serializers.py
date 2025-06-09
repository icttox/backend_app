from rest_framework import serializers
from .models import (
    ProductTemplate, Cliente, Cotizacion, ProductoCotizacion,
    CotizadorImagenproducto, Kit, KitProducto
)
from .cache.models import ProductsCache
from decimal import Decimal

class EmptyStringCharField(serializers.CharField):
    def to_representation(self, value):
        if value is None:
            return ""
        return super().to_representation(value)

class EmptyStringURLField(serializers.URLField):
    def to_representation(self, value):
        if value is None:
            return ""
        return super().to_representation(value)

class ProductTemplateSerializer(serializers.ModelSerializer):
    type_name = EmptyStringCharField(source='type.name', read_only=True)
    family_name = EmptyStringCharField(source='family.name', read_only=True)
    line_name = EmptyStringCharField(source='line.name', read_only=True)
    group_name = EmptyStringCharField(source='group.name', read_only=True)
    imagen = serializers.SerializerMethodField()

    def get_imagen(self, obj):
        if hasattr(obj, '_prefetched_imagen'):
            return obj._prefetched_imagen.url if obj._prefetched_imagen else ""
            
        imagen = CotizadorImagenproducto.objects.filter(
            clave_padre=obj.reference_mask
        ).only('url').first()
        return imagen.url if imagen else ""

    class Meta:
        model = ProductTemplate
        fields = [
            'id', 
            'active', 
            'is_line', 
            'type',
            'reference_mask',
            'name',
            'type_name',
            'family_name',
            'line_name',
            'group_name',
            'imagen'
        ]

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class ProductoCotizacionSerializer(serializers.ModelSerializer):
    cotizacion_uuid = serializers.UUIDField(source='cotizacion.uuid')
    cantidad = serializers.IntegerField(required=False, default=1)
    porcentaje_descuento = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    precio_lista = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    costo = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    precio_descuento = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    margen = serializers.IntegerField(required=False, default=0)
    importe = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    clave = EmptyStringCharField(max_length=50, allow_blank=True, required=False)
    descripcion = EmptyStringCharField(max_length=255, allow_blank=True, required=False)
    imagen_url = EmptyStringCharField(allow_blank=True, required=False)
    linea = EmptyStringCharField(max_length=100, allow_blank=True, required=False)
    familia = EmptyStringCharField(max_length=100, allow_blank=True, required=False)
    grupo = EmptyStringCharField(max_length=100, allow_blank=True, required=False)
    tag = EmptyStringCharField(allow_blank=True, required=False)
    producto_id = serializers.IntegerField(required=False, allow_null=True)
    padre = serializers.BooleanField(required=False, default=False)
    route_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ProductoCotizacion
        fields = [
            'id',
            'cotizacion_uuid',
            'kit_uuid',
            'es_kit',
            'especial',
            'padre',
            'clave',
            'descripcion',
            'imagen_url',
            'linea',
            'familia',
            'grupo',
            'tag',
            'producto_id',
            'cantidad',
            'porcentaje_descuento',
            'precio_lista',
            'costo',
            'precio_descuento',
            'margen',
            'importe',
            'route_id'
        ]

    def create(self, validated_data):
        cotizacion_data = validated_data.pop('cotizacion')
        try:
            cotizacion = Cotizacion.objects.get(uuid=cotizacion_data['uuid'])
            validated_data['cotizacion'] = cotizacion
            
            return super().create(validated_data)
        except Cotizacion.DoesNotExist:
            raise serializers.ValidationError({'cotizacion_uuid': 'Cotización no encontrada'})

    def validate_porcentaje_descuento(self, value):
        # Se eliminó la validación para permitir valores negativos y superiores a 100
        return value

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0")
        return value

class ClienteInfoSerializer(serializers.Serializer):
    cliente = serializers.CharField()
    persona_contacto = serializers.CharField()
    email_cliente = serializers.EmailField()
    telefono_cliente = serializers.CharField() 

class VendedorInfoSerializer(serializers.Serializer):
    vendedor = serializers.CharField()
    email_vendedor = serializers.EmailField()
    telefono_vendedor = serializers.CharField()

class OperacionesSerializer(serializers.Serializer):
    subtotal_mobiliario = serializers.DecimalField(max_digits=18, decimal_places=6)
    total_descuento = serializers.DecimalField(max_digits=18, decimal_places=6)
    logistica = serializers.DecimalField(max_digits=18, decimal_places=6)
    iva = serializers.DecimalField(max_digits=18, decimal_places=6)
    total_general = serializers.DecimalField(max_digits=18, decimal_places=6)

class ConfiguracionPDFSerializer(serializers.Serializer):
    tiempo_entrega = serializers.CharField()
    vigencia = serializers.CharField()
    condiciones_pago = serializers.CharField()
    mostrar_clave = serializers.BooleanField()
    mostrar_precio_lista = serializers.BooleanField()
    mostrar_precio_descuento = serializers.BooleanField()
    mostrar_logistica = serializers.BooleanField()
    mostrar_descuento_total = serializers.BooleanField()

class CotizacionSerializer(serializers.ModelSerializer):
    productos = ProductoCotizacionSerializer(many=True, read_only=True)
    
    # Verificar si los campos de usuario existen en la base de datos
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(
        """SELECT column_name FROM information_schema.columns 
           WHERE table_name = 'cotizador_cotizacion' 
           AND column_name = 'usuario_creacion_id'"""
    )
    usuario_fields_exist = bool(cursor.fetchone())

    class Meta:
        model = Cotizacion
        fields = [
            'uuid',
            'folio',
            'version',
            'proyecto',
            'fecha_proyecto',
            'unidad_facturacion',
            'proyectista',
            'estatus',
            'motivo',
            'fecha_creacion',
            'fecha_modificacion',
            # Cliente info
            'cliente',
            'cliente_id',
            'persona_contacto',
            'email_cliente',
            'telefono_cliente',
            # Vendedor info
            'vendedor',
            'vendedor_id',
            'email_vendedor',
            'telefono_vendedor',
            # Usuario info
            'usuario_id',
            'usuario_email',
            # Operaciones
            'subtotal_mobiliario',
            'total_descuento',
            'logistica',
            'iva',
            'total_general',
            # Configuración PDF
            'tiempo_entrega',
            'vigencia',
            'condiciones_pago',
            'mostrar_clave',
            'mostrar_precio_lista',
            'mostrar_precio_descuento',
            'mostrar_logistica',
            'mostrar_descuento_total',
            # Odoo SO
            'odoo_so',
            # HubSpot Deal ID
            'hs_deal_id',
            # Productos
            'productos'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Añadir campos de usuario solo si existen en la base de datos
        if self.__class__.usuario_fields_exist:
            self.fields['usuario_creacion'] = serializers.PrimaryKeyRelatedField(read_only=True)
            self.fields['usuario_envio'] = serializers.PrimaryKeyRelatedField(read_only=True)
            self.fields['usuario_aprobacion'] = serializers.PrimaryKeyRelatedField(read_only=True)
            self.fields['usuario_rechazo'] = serializers.PrimaryKeyRelatedField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Agrupar información del cliente
        data['cliente_info'] = {
            'cliente': data.pop('cliente'),
            'cliente_id': data.pop('cliente_id'),
            'persona_contacto': data.pop('persona_contacto'),
            'email_cliente': data.pop('email_cliente'),
            'telefono_cliente': data.pop('telefono_cliente')
        }
        
        # Agrupar información del vendedor
        data['vendedor_info'] = {
            'vendedor': data.pop('vendedor'),
            'vendedor_id': data.pop('vendedor_id'),
            'email_vendedor': data.pop('email_vendedor'),
            'telefono_vendedor': data.pop('telefono_vendedor')
        }
        
        # Agrupar operaciones
        data['operaciones'] = {
            'subtotal_mobiliario': data.pop('subtotal_mobiliario'),
            'total_descuento': data.pop('total_descuento'),
            'logistica': data.pop('logistica'),
            'iva': data.pop('iva'),
            'total_general': data.pop('total_general')
        }
        
        # Agrupar configuración PDF
        data['configuracion_pdf'] = {
            'tiempo_entrega': data.pop('tiempo_entrega'),
            'vigencia': data.pop('vigencia'),
            'condiciones_pago': data.pop('condiciones_pago'),
            'mostrar_clave': data.pop('mostrar_clave'),
            'mostrar_precio_lista': data.pop('mostrar_precio_lista'),
            'mostrar_precio_descuento': data.pop('mostrar_precio_descuento'),
            'mostrar_logistica': data.pop('mostrar_logistica'),
            'mostrar_descuento_total': data.pop('mostrar_descuento_total')
        }
        
        # Agrupar información del usuario
        data['usuario_info'] = {
            'usuario_id': data.pop('usuario_id'),
            'usuario_email': data.pop('usuario_email')
        }
        
        return data

    def create(self, validated_data):
        # Manejar campos que pueden venir en la solicitud pero no en validated_data
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            # Manejar cliente_id
            if 'cliente_id' in request.data:
                validated_data['cliente_id'] = request.data.get('cliente_id')
            
            # Manejar usuario_id y usuario_email
            if 'usuario_id' in request.data:
                validated_data['usuario_id'] = request.data.get('usuario_id')
            if 'usuario_email' in request.data:
                validated_data['usuario_email'] = request.data.get('usuario_email')
            
        instance = Cotizacion.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        # Manejar campos que pueden venir en la solicitud pero no en validated_data
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            # Manejar cliente_id
            if 'cliente_id' in request.data:
                validated_data['cliente_id'] = request.data.get('cliente_id')
            
            # Manejar usuario_id y usuario_email
            if 'usuario_id' in request.data:
                validated_data['usuario_id'] = request.data.get('usuario_id')
            if 'usuario_email' in request.data:
                validated_data['usuario_email'] = request.data.get('usuario_email')
            
        return super().update(instance, validated_data)

class CotizadorImagenproductoSerializer(serializers.ModelSerializer):
    clave_padre = EmptyStringCharField(max_length=255)
    url = EmptyStringURLField()

    class Meta:
        model = CotizadorImagenproducto
        fields = ['id', 'clave_padre', 'url']

class KitProductoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo KitProducto"""
    producto_nombre = serializers.SerializerMethodField()
    producto_imagen = serializers.SerializerMethodField()
    tag = serializers.CharField(max_length=255, allow_blank=True, required=False)
    
    class Meta:
        model = KitProducto
        fields = [
            'id', 'kit', 'clave', 'cantidad', 'porcentaje_descuento',
            'precio_lista', 'costo', 'precio_descuento', 'importe',
            'orden', 'producto_nombre', 'producto_imagen',
            'descripcion', 'linea', 'familia', 'grupo', 'tag', 'producto_id',
            'especial', 'padre', 'mostrar_en_kit', 'es_opcional', 'route_id'
        ]
    
    def get_producto_nombre(self, obj):
        return obj.get_producto_nombre()
    
    def get_producto_imagen(self, obj):
        return obj.get_producto_imagen()

class KitProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear o actualizar un KitProducto"""
    producto_imagen = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = KitProducto
        fields = [
            'orden','clave', 'cantidad', 'porcentaje_descuento',
            'precio_lista', 'costo', 'importe','descripcion', 'linea', 'familia', 'grupo', 'tag', 'mostrar_en_kit','es_opcional', 'producto_id', 'producto_imagen', 'especial', 'padre', 'route_id'
        ]
        read_only_fields = ['precio_descuento', 'importe']

class KitSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Kit.
    """
    productos = KitProductoSerializer(many=True, read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Kit
        fields = [
            'id', 'uuid', 'nombre', 'descripcion', 'imagen_url', 'tag', 'cantidad',
            'valor_unitario', 'costo_unitario', 'porcentaje_descuento',
            'valor_unitario_con_descuento', 'creado_por', 'creado_por_nombre',
            'productos'
        ]
    
    def get_creado_por_nombre(self, obj):
        """
        Obtiene el nombre del usuario que creó el kit
        """
        if obj.creado_por:
            return f"{obj.creado_por.first_name} {obj.creado_por.last_name}".strip() or obj.creado_por.username
        return None


class KitCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar kits sin incluir los productos.
    """
    class Meta:
        model = Kit
        fields = [
            'uuid', 'nombre', 'descripcion', 'imagen_url', 'tag', 'cantidad',
            'valor_unitario', 'costo_unitario', 'porcentaje_descuento',
            'valor_unitario_con_descuento'
        ]
        extra_kwargs = {
            'uuid': {'read_only': True},
            'nombre': {'required': True},
            'descripcion': {'required': False},
            'imagen_url': {'required': False},
            'tag': {'required': False},
            'cantidad': {'required': False, 'default': 1},
            'valor_unitario': {'required': False, 'default': 0},
            'costo_unitario': {'required': False, 'default': 0},
            'porcentaje_descuento': {'required': False, 'default': 0},
            'valor_unitario_con_descuento': {'required': False, 'default': 0}
        }
    
    def create(self, validated_data):
        # Asignar el usuario actual como creador del kit
        user = self.context['request'].user
        validated_data['creado_por'] = user
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        # Asegurarse de que el UUID no se modifique durante la actualización
        # y que todos los campos se actualicen correctamente
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.imagen_url = validated_data.get('imagen_url', instance.imagen_url)
        instance.cantidad = validated_data.get('cantidad', instance.cantidad)
        instance.valor_unitario = validated_data.get('valor_unitario', instance.valor_unitario)
        instance.costo_unitario = validated_data.get('costo_unitario', instance.costo_unitario)
        instance.porcentaje_descuento = validated_data.get('porcentaje_descuento', instance.porcentaje_descuento)
        instance.valor_unitario_con_descuento = validated_data.get('valor_unitario_con_descuento', instance.valor_unitario_con_descuento)
        
        instance.save()
        return instance


class ApplyKitToCotizacionSerializer(serializers.Serializer):
    """
    Serializer para aplicar un kit a una cotización.
    Permite especificar valores personalizados para el kit en la cotización.
    """
    kit_uuid = serializers.UUIDField(
        required=True,
        help_text="UUID del kit a aplicar"
    )
    mostrar_productos_individuales = serializers.BooleanField(
        default=True,
        help_text="Si es True, muestra los productos individuales del kit en la cotización"
    )
    porcentaje_descuento_adicional = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de descuento adicional a aplicar al kit completo"
    )
    # Campos opcionales para personalizar el kit en la cotización
    cantidad = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Cantidad personalizada del kit para esta cotización"
    )
    valor_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
        help_text="Valor unitario personalizado del kit para esta cotización"
    )
    costo_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
        help_text="Costo unitario personalizado del kit para esta cotización"
    )
    porcentaje_descuento = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Porcentaje de descuento personalizado del kit para esta cotización"
    )
    valor_unitario_con_descuento = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
        help_text="Valor unitario con descuento personalizado del kit para esta cotización"
    )

    def validate_kit_uuid(self, value):
        """
        Valida que el kit exista.
        """
        try:
            Kit.objects.get(uuid=value)
            return value
        except Kit.DoesNotExist:
            raise serializers.ValidationError("El kit especificado no existe.")


class KitImageUploadSerializer(serializers.Serializer):
    """
    Serializer para la carga de imágenes de kits.
    """
    image = serializers.ImageField(
        help_text="Archivo de imagen a cargar",
        required=True
    )
    
    def validate_image(self, value):
        """
        Validar que el archivo sea una imagen y tenga un tamaño adecuado.
        """
        # Verificar el tipo de archivo
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError(
                "El archivo debe ser una imagen (JPEG, PNG, etc.)"
            )
        
        # Verificar el tamaño (máximo 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "El tamaño de la imagen no debe exceder 5MB"
            )
        
        return value

class OrderLineItemSerializer(serializers.Serializer):
    """
    Serializer para los items de línea de una orden.
    """
    product_id = serializers.IntegerField(required=True)
    product_uom_qty = serializers.IntegerField(required=True)
    price_unit = serializers.DecimalField(max_digits=16, decimal_places=8, required=True)  # Aumentado de 12 a 16 para permitir valores mu00e1s grandes
    route_id = serializers.IntegerField(required=False, allow_null=True)  # Agregar campo route_id

class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer para crear órdenes en Odoo.
    """
    partner_id = serializers.IntegerField(required=True)
    client_order_ref = serializers.CharField(required=True, allow_blank=False, error_messages={'blank': 'El campo Folio de Cotización es obligatorio. Por favor, complételo.', 'required': 'El campo Folio de Cotización es obligatorio. Por favor, complételo.'})
    priority = serializers.CharField(required=False, default="replenishment")
    manufacture = serializers.CharField(required=False, default="replenishment")
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)  # Agregar campo warehouse
    fiscal_position_id = serializers.IntegerField(required=False, allow_null=True)  # Agregar campo fiscal_position_id
    analytic_account_id = serializers.IntegerField(required=False, allow_null=True)  # Agregar campo analytic_account_id
    hubspot_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)  # Agregar campo hubspot_id
    vendedor_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)  # Agregar campo vendedor_id
    products = serializers.ListField(
        child=OrderLineItemSerializer(),
        required=True
    )
    
    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError("Debe proporcionar al menos un producto")
        return value

    
    def to_odoo_format(self, validated_data=None):
        # Si no se proporciona validated_data, usar self.validated_data
        data = validated_data if validated_data is not None else self.validated_data
        
        # Extraer productos del payload
        products = data.get('products', [])
        
        # Convertir la lista de productos al formato que espera Odoo [0, 0, {...}]
        order_line = []
        for product in products:
            print(f"Procesando producto - ID: {product.get('product_id')}, route_id: {product.get('route_id')}")
            line = [0, 0, {
                'product_id': product['product_id'],
                'product_uom_qty': product['product_uom_qty'],
                'price_unit': product['price_unit'],
                'route_id': product.get('route_id')
            }]
            order_line.append(line)
            
        # Asegurarse de que todos los campos necesarios estén presentes
        # Usar vendedor_id como user_id si está disponible
        user_id = data.get('vendedor_id', False)
        print(f"vendedor_id: {type(user_id)}")
        

        if user_id is not None and user_id != False:
            if isinstance(user_id, str):
                if user_id.isdigit():
                    user_id = int(user_id)
                # Si es string pero no es un dígito, dejarlo como string
            # Si ya es un entero, no hacer nada
        
        result = {
            'user_id': user_id,  # Usar el vendedor_id como user_id
            'partner_id': data['partner_id'],
            'client_order_ref': data['client_order_ref'],
            'priority': data.get('priority', 'replenishment'),
            'manufacture': data.get('manufacture', 'replenishment'),
            'warehouse_id': data.get('warehouse_id'),  # Corregido de 'warehouse' a 'warehouse_id'
            'fiscal_position_id': data.get('fiscal_position_id', 3),
            'analytic_account_id': data.get('analytic_account_id'),
            'hubspot_id': data.get('hubspot_id'),
            'vendedor_id': data.get('vendedor_id'),
            'note': "",
            'order_line': order_line
        }
        
        # Agregar notas adicionales
        cotizacion = None
        uuid = data.get('uuid')
        if uuid:
            from .models import Cotizacion
            try:
                cotizacion = Cotizacion.objects.get(uuid=uuid)
                print(f"Cotizaciu00f3n encontrada en el serializador: ID={cotizacion.id}, UUID={cotizacion.uuid}")
            except Cotizacion.DoesNotExist:
                print(f"No se encontru00f3 cotizaciu00f3n con UUID={uuid}")
                # Simplemente continuamos con cotizacion = None
                pass
        else:
            print("No se proporcionu00f3 UUID en los datos")
        
        notes = []

        notes.append("\nMETA DATOS DE LA COTIZACION")
        # Verificar si cotizacion existe antes de acceder a sus atributos
        if cotizacion:
            notes.append(f"Folio: {cotizacion.folio}")
            if hasattr(cotizacion, 'proyecto') and cotizacion.proyecto:
                notes.append(f"Proyecto: {cotizacion.proyecto}")
            if hasattr(cotizacion, 'cliente') and cotizacion.cliente:
                notes.append(f"Cliente: {cotizacion.cliente}")
            if hasattr(cotizacion, 'fecha_creacion') and cotizacion.fecha_creacion:
                notes.append(f"Fecha de creacion: {cotizacion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}")
            if hasattr(cotizacion, 'estatus') and cotizacion.estatus:
                notes.append(f"Estatus: {cotizacion.estatus}")
            notes.append(f"UUID: {cotizacion.uuid}")
        else:
            notes.append("No se encontro informacion de la cotizacion")
            notes.append(f"UUID proporcionado: {uuid}")
            notes.append(f"Referencia del cliente: {data.get('client_order_ref', 'N/A')}")
        
        # Agregar la fecha y hora actual
        from datetime import datetime
        import pytz
        from django.conf import settings

        tz = pytz.timezone(settings.TIME_ZONE)
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        notes.append(f"Fecha y hora de envio: {current_time}")
        
        # Informacion del vendedor (solo si cotizacion existe y tiene vendedor)
        if cotizacion:
            notes.append(f"\nINFORMACION DEL VENDEDOR:")
            # Verificar si tiene vendedor
            if hasattr(cotizacion, 'vendedor') and cotizacion.vendedor:
                notes.append(f"Nombre: {cotizacion.vendedor}")
                if hasattr(cotizacion, 'email_vendedor') and cotizacion.email_vendedor:
                    notes.append(f"Email: {cotizacion.email_vendedor}")
                if hasattr(cotizacion, 'telefono_vendedor') and cotizacion.telefono_vendedor:
                    notes.append(f"Teléfono: {cotizacion.telefono_vendedor}")
            # Si no tiene vendedor, verificar si tiene usuario_creacion
            elif hasattr(cotizacion, 'usuario_creacion') and cotizacion.usuario_creacion:
                notes.append(f"Nombre: {cotizacion.usuario_creacion.first_name} {cotizacion.usuario_creacion.last_name}")
                notes.append(f"Email: {cotizacion.usuario_creacion.email}")
                if hasattr(cotizacion.usuario_creacion, 'unidad') and cotizacion.usuario_creacion.unidad:
                    notes.append(f"Unidad: {cotizacion.usuario_creacion.unidad}")
            # Si no tiene usuario_creacion, verificar si tiene usuario_id o usuario_email
            elif hasattr(cotizacion, 'usuario_id') and cotizacion.usuario_id:
                notes.append(f"ID: {cotizacion.usuario_id}")
                if hasattr(cotizacion, 'usuario_email') and cotizacion.usuario_email:
                    notes.append(f"Email: {cotizacion.usuario_email}")
            else:
                notes.append("No hay información disponible del vendedor")
        else:
            notes.append(f"\nINFORMACION DEL VENDEDOR: No disponible")
        
        # Informacion del almacen seleccionado
        notes.append(f"\nINFORMACION DE LA ORDEN:")
        notes.append(f"Almacen seleccionado: {data.get('warehouse_id') or 'No especificado'}")
        notes.append(f"Numero de productos: {len(products)}")
        
        # Unir todas las notas en un solo texto
        note_text = "\n".join(notes)
        
        result['note'] = note_text
        
        return result
