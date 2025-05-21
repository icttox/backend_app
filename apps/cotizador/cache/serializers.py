from rest_framework import serializers
from .models import ProductsCache
from apps.cotizador.models import CotizadorImagenproducto

class ProductsCacheSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo ProductsCache.
    """
    class Meta:
        model = ProductsCache
        fields = [
            'id', 'name', 'reference_mask', 'type_id', 'family_id',
            'line_id', 'group_id', 'active', 'is_line', 'description_sale',
            'default_code', 'type_name', 'family_name', 'line_name',
            'group_name', 'image_url', 'last_sync'
        ]
        read_only_fields = fields  # Todos los campos son de solo lectura ya que es una caché

class ProductImageUploadSerializer(serializers.Serializer):
    """
    Serializador para la carga de imágenes de productos.
    """
    image = serializers.ImageField(
        help_text="Archivo de imagen a cargar",
        required=True
    )
    reference_mask = serializers.CharField(
        help_text="Identificador único del producto (reference_mask)",
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
    
    def validate_reference_mask(self, value):
        """
        Validar que el reference_mask corresponda a un producto existente.
        """
        product = ProductsCache.objects.filter(reference_mask=value).first()
        if not product:
            raise serializers.ValidationError(
                f"No se encontró ningún producto con reference_mask: {value}"
            )
        
        return value
