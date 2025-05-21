from rest_framework import serializers
from .models import (
    Categoria,
    Almacen,
    PropuestaCompra,
    ItemPropuestaCompra
)
from apps.accounts.serializers import UserSerializer
from apps.accounts.models import User, UserProfile

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class UserComprasSerializer(serializers.ModelSerializer):
    """Serializer para manejar las categoru00edas de compras asignadas a un usuario"""
    usuario_details = UserSerializer(source='user', read_only=True)
    categorias_compras = CategoriaSerializer(source='categorias_compras_asignadas', read_only=True, many=True)
    categorias_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'usuario_details', 'nombre_comprador', 'categorias_compras_asignadas', 
                 'categorias_compras', 'categorias_count')
    
    def get_categorias_count(self, obj):
        return obj.categorias_compras_asignadas.count()

class AlmacenSerializer(serializers.Serializer):
    """
    Serializador para la clase proxy Almacen que interactúa con la API externa.
    Define manualmente los campos esperados en la respuesta de la API.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True, required=False, allow_blank=True, allow_null=True)
    active = serializers.BooleanField(read_only=True, default=True)
    
    # Campos adicionales que podrían venir en los datos de la API
    classification = serializers.JSONField(read_only=True, required=False)
    parent_id = serializers.IntegerField(read_only=True, required=False, allow_null=True)
    location_id = serializers.IntegerField(read_only=True, required=False, allow_null=True)

class ItemPropuestaCompraSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # Make required=False for create/updates where ID might not be provided initially

    class Meta:
        model = ItemPropuestaCompra
        fields = '__all__'
        read_only_fields = (
            'propuesta', 'fecha_creacion', 'fecha_actualizacion'
        )

class ItemPropuestaCompraCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear items de propuesta con datos básicos"""
    class Meta:
        model = ItemPropuestaCompra
        fields = (
            'categoria', 'codigo', 'producto', 'medida',
            'costo', 'existencia', 'comprometido', 'libre', 'consumo_mensual', 'inv_mensuales',
            'cantidad_oc', # Added cantidad_oc field
            'registrar', 'produccion', 'cantidad_propuesta',
            'meses', 'comentarios', 'product_id', 'medida_id', 'currency_id'
        )

class PropuestaCompraListSerializer(serializers.ModelSerializer):
    """Serializer para listar propuestas de compra con sus items"""
    comprador_nombre = serializers.SerializerMethodField()
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    cantidad_lineas = serializers.SerializerMethodField()
    proveedor = serializers.ReadOnlyField(source='proveedor.nombre')
    items = ItemPropuestaCompraSerializer(many=True, read_only=True)
    
    class Meta:
        model = PropuestaCompra
        fields = (
            'id', 'comprador', 'comprador_nombre', 'estado', 'estado_display',
            'fecha_creacion', 'fecha_envio', 'fecha_aprobacion_rechazo', 'cantidad_lineas',
            'proveedor', 'items', 'historial_eventos', # Reemplazado comentarios
            'almacenes_ids', 'categoria_id', 'categoria_nombre',
            'fecha_registro_odoo', 'odoo_purchase_order_id', 'odoo_response' # Added new fields
        )
    
    def get_cantidad_lineas(self, obj):
        return obj.items.count()
        
    def get_comprador_nombre(self, obj):
        if not obj.comprador:
            return None
            
        try:
            # Try to get the profile directly
            profile = obj.comprador.profile
            if profile and profile.nombre_comprador:
                return profile.nombre_comprador
                
            # If profile exists but nombre_comprador is empty, use user's full name
            if profile:
                full_name = obj.comprador.get_full_name()
                if full_name.strip():
                    return full_name
                return obj.comprador.username
        except Exception:
            # Fallback to user's full name or username if profile access fails
            full_name = obj.comprador.get_full_name()
            if full_name.strip():
                return full_name
            return obj.comprador.username

class PropuestaCompraDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para una propuesta de compra con sus líneas"""
    # Detalles de los usuarios relacionados
    comprador_details = UserSerializer(source='comprador', read_only=True)
    usuario_aprobador_details = UserSerializer(source='usuario_aprobador', read_only=True)

    # Serializador para los items (REMOVED read_only=True)
    items = ItemPropuestaCompraSerializer(many=True)
    # Campo calculado para el estado
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    # Campo calculado para detalles de almacenes (si aplica)
    # almacenes_details = serializers.SerializerMethodField()

    class Meta:
        model = PropuestaCompra
        fields = '__all__' # Incluye todos los campos del modelo, incluyendo historial_eventos
        read_only_fields = (
            # Campos que no deben ser modificables directamente a través de este serializer detallado
            'id', # Generalmente el ID es read-only post-creación
            'fecha_creacion', 'fecha_actualizacion', 'fecha_envio',
            'fecha_aprobacion_rechazo', 'estado_display',
            'comprador_details', 'usuario_aprobador_details',
            'historial_eventos', # historial_eventos es gestionado por el modelo
            'fecha_registro_odoo', 'odoo_purchase_order_id', # Added new fields as read-only
            # 'items' REMOVED from here if it was present
            # 'almacenes_details', # Si se usa SerializerMethodField, es inherentemente read-only
        )

class PropuestaCompraCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear una propuesta de compra con sus líneas"""
    items = ItemPropuestaCompraCreateSerializer(many=True)
    # historial_eventos no se incluye aquí ya que se poblará mediante acciones del modelo.
    # Si se necesita un comentario inicial al crear, se podría añadir un campo no-modelo aquí
    # y manejarlo en la vista o en el método create del serializer.
    
    class Meta:
        model = PropuestaCompra
        fields = (
            'id', 'comprador', 'proveedor', 'items', # 'comentarios' eliminado
            'almacenes_ids', 'categoria_id', 'categoria_nombre' 
        )
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        propuesta = PropuestaCompra.objects.create(**validated_data)
        
        for item_data in items_data:
            ItemPropuestaCompra.objects.create(propuesta=propuesta, **item_data)
        
        return propuesta

class PropuestaCompraUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar una propuesta de compra"""
    items = ItemPropuestaCompraSerializer(many=True, required=False) # required=False allows updates without sending items

    class Meta:
        model = PropuestaCompra
        # 'comentarios' eliminado, 'historial_eventos' es read_only y se maneja por el modelo
        fields = ('estado', 'proveedor', 'items') 
        read_only_fields = (
            'id', 'comprador', 'fecha_creacion', 'fecha_actualizacion',
            'fecha_envio', 'fecha_aprobacion_rechazo', 'usuario_aprobador',
            'historial_eventos', 'fecha_registro_odoo', 'odoo_purchase_order_id', 'odoo_response'
        )
    
    def validate_estado(self, value):
        # Validar transiciones de estado permitidas
        if self.instance.estado == PropuestaCompra.ESTADO_BORRADOR:
            if value not in [PropuestaCompra.ESTADO_ENVIADA, PropuestaCompra.ESTADO_BORRADOR]:
                raise serializers.ValidationError(
                    f"Desde el estado 'Borrador' solo puede cambiar a 'Enviada' o seguir como 'Borrador'"
                )
        elif self.instance.estado == PropuestaCompra.ESTADO_ENVIADA:
            if value not in [
                PropuestaCompra.ESTADO_APROBADA,
                PropuestaCompra.ESTADO_RECHAZADA,
                PropuestaCompra.ESTADO_SOLICITAR_MODIFICACION,
                PropuestaCompra.ESTADO_ENVIADA
            ]:
                raise serializers.ValidationError(
                    f"Desde el estado 'Enviada' solo puede cambiar a 'Aprobada', 'Rechazada' o 'Solicitar modificación'"
                )
        elif self.instance.estado == PropuestaCompra.ESTADO_APROBADA:
            if value != self.instance.estado:
                raise serializers.ValidationError(
                    f"No se puede cambiar el estado de una propuesta ya aprobada"
                )
        elif self.instance.estado == PropuestaCompra.ESTADO_RECHAZADA:
            # Permitir que una propuesta rechazada pueda volver a borrador o ser enviada
            if value not in [PropuestaCompra.ESTADO_BORRADOR, PropuestaCompra.ESTADO_ENVIADA, PropuestaCompra.ESTADO_RECHAZADA]:
                raise serializers.ValidationError(
                    f"Desde el estado 'Rechazada' solo puede cambiar a 'Borrador', 'Enviada' o seguir como 'Rechazada'"
                )
        return value

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        instance = super().update(instance, validated_data) # Update PropuestaCompra fields first

        if items_data is not None:
            # Dictionary to keep track of item IDs present in the input
            input_item_ids = {item_data.get('id') for item_data in items_data if item_data.get('id') is not None}
            
            # Update existing items and identify items to potentially create/delete
            for item_data in items_data:
                item_id = item_data.get('id')
                
                if item_id:
                    try:
                        item_instance = ItemPropuestaCompra.objects.get(id=item_id, propuesta=instance)
                        # Use the item serializer to update the instance
                        item_serializer = ItemPropuestaCompraSerializer(item_instance, data=item_data, partial=True)
                        if item_serializer.is_valid(raise_exception=True):
                            item_serializer.save()
                            item_instance.refresh_from_db()
                        else:
                            print(f"WARNING: Item with id {item_id} provided in update payload but not found in proposal {instance.id}.")
                            pass # Or raise error
                    except ItemPropuestaCompra.DoesNotExist:
                        print(f"WARNING: Item with id {item_id} provided in update payload but not found in proposal {instance.id}.")
                        pass # Or raise error
                else:
                    # Handle items without ID if necessary (e.g., allow creating items via PUT?)
                    # Usually for PUT, you only update existing items identified by ID.
                    print(f"WARNING: Skipping item update because ID is missing: {item_data.get('codigo')}")
                    pass

            # Optional: Delete items present in DB but not in the input payload
            # If PUT should enforce exact representation, uncomment the next line:
            # instance.items.exclude(id__in=input_item_ids).delete()
            
        return instance
