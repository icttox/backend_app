from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.html import mark_safe
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.contrib.auth.models import User

class Cliente(models.Model):
    """Modelo para almacenar información de clientes"""
    partner_id = models.IntegerField(primary_key=True, help_text="ID único del cliente")
    name_partner = models.CharField(max_length=255, help_text="Nombre del cliente")
    rfc = models.CharField(max_length=20, blank=True, null=True, help_text="RFC del cliente")


    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        db_table = 'cotizador_cliente'  # Nombre de la tabla en la base de datos
        indexes = [
            models.Index(fields=['name_partner'], name='idx_cliente_name'),
            models.Index(fields=['rfc'], name='idx_cliente_rfc'),
        ]

    def __str__(self):
        return f"{self.name_partner}"

class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    codigo_producto = models.CharField(max_length=64, unique=True, null=True, blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo_producto} - {self.nombre}"

class ProductType(models.Model):
    """Modelo para product_type de Odoo"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'product_type'
        app_label = 'cotizador'

    def __str__(self):
        return self.name

class ProductFamily(models.Model):
    """Modelo para product_family de Odoo"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'product_family'
        app_label = 'cotizador'

    def __str__(self):
        return self.name

class ProductLine(models.Model):
    """Modelo para product_line de Odoo"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'product_line'
        app_label = 'cotizador'

    def __str__(self):
        return self.name

class ProductGroup(models.Model):
    """Modelo para product_group de Odoo"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'product_group'
        app_label = 'cotizador'

    def __str__(self):
        return self.name

class ProductTemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_line=True,
            reference_mask__isnull=False,
            active=True
        )

    def get_full_queryset(self):
        """
        Obtiene todos los registros sin filtros
        """
        return super().get_queryset()

class ProductTemplate(models.Model):
    """Modelo que almacena una copia local de los productos de Odoo"""
    objects = ProductTemplateManager()  # Hacer que el manager filtrado sea el predeterminado
    all_objects = models.Manager()  # Manager secundario para acceder a todos los registros

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    reference_mask = models.CharField(max_length=255, null=True, db_index=True)
    note_pricelist = models.CharField(max_length=255, null=True, blank=True)
    type = models.ForeignKey(ProductType, on_delete=models.SET_NULL, null=True, db_index=True)
    family = models.ForeignKey(ProductFamily, on_delete=models.SET_NULL, null=True, db_index=True)
    line = models.ForeignKey(ProductLine, on_delete=models.SET_NULL, null=True, db_index=True)
    group = models.ForeignKey(ProductGroup, on_delete=models.SET_NULL, null=True, db_index=True)
    is_line = models.BooleanField(default=True, db_index=True)
    pricelist = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Ahora es gestionado localmente
        db_table = 'product_template'  # Nueva tabla local
        app_label = 'cotizador'
        indexes = [
            models.Index(fields=['name'], name='idx_name'),
            models.Index(fields=['reference_mask'], name='idx_ref_mask'),
            models.Index(fields=['is_line', 'active'], name='idx_line_active'),
            models.Index(fields=['type', 'family', 'line', 'group'], name='idx_product_hierarchy')
        ]

    def __str__(self):
        return f"{self.reference_mask} - {self.name}"

    def get_images(self):
        """
        Obtiene todas las imágenes asociadas a este producto a través del reference_mask
        """
        return CotizadorImagenproducto.objects.filter(clave_padre=self.reference_mask)

    def get_primary_image(self):
        """
        Obtiene la primera imagen asociada al producto
        """
        return self.get_images().first()

    def get_image_preview(self):
        """
        Retorna el HTML para mostrar la vista previa de la primera imagen
        """
        image = self.get_primary_image()
        if image and image.url:
            return mark_safe(f'<img src="{image.url}" style="max-height: 50px;" />')
        return '-'

    def get_image_gallery(self):
        """
        Retorna el HTML para mostrar todas las imágenes del producto
        """
        images = self.get_images()
        if images:
            gallery_html = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
            for image in images:
                if image.url:
                    gallery_html += f'<img src="{image.url}" style="max-height: 100px;" />'
            gallery_html += '</div>'
            return mark_safe(gallery_html)
        return 'No hay imágenes disponibles'

# Estados de cotización
ESTADO_BORRADOR = 'BORRADOR'
ESTADO_EN_REVISION = 'EN_REVISION'
ESTADO_ACEPTADA = 'ACEPTADA'
ESTADO_RECHAZADA = 'RECHAZADA'
ESTADO_CANCELADA = 'CANCELADA'

ESTADO_CHOICES = [
    (ESTADO_BORRADOR, 'Borrador'),
    (ESTADO_EN_REVISION, 'En Revisión'),
    (ESTADO_ACEPTADA, 'Aceptada'),
    (ESTADO_RECHAZADA, 'Rechazada'),
    (ESTADO_CANCELADA, 'Cancelada'),
]

class Cotizacion(models.Model):
    ESTATUS_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ]

    # Campos de control
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    folio = models.CharField(max_length=50, blank=True, default='')
    version = models.IntegerField(default=1)
    
    # Campos principales
    proyecto = models.CharField(max_length=255, blank=True, default='')
    fecha_proyecto = models.DateField(null=True, blank=True)
    cliente = models.CharField(max_length=255, blank=True, default='')
    cliente_id = models.CharField(max_length=50, blank=True, default='')
    persona_contacto = models.CharField(max_length=255, blank=True, default='')
    email_cliente = models.EmailField(blank=True, default='')
    telefono_cliente = models.CharField(max_length=20, blank=True, default='')
    vendedor = models.CharField(max_length=255, blank=True, default='')
    vendedor_id = models.CharField(max_length=50, blank=True, default='')
    email_vendedor = models.EmailField(blank=True, default='')
    telefono_vendedor = models.CharField(max_length=20, blank=True, default='')
    proyectista = models.CharField(max_length=255, blank=True, default='')
    unidad_facturacion = models.CharField(max_length=50, blank=True, default='')
    usuario_id = models.CharField(max_length=50, blank=True, default='')
    usuario_email = models.EmailField(blank=True, default='')
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='borrador')
    motivo = models.TextField(blank=True, default='')
    
    # Campos de configuración PDF
    tiempo_entrega = models.CharField(max_length=255, blank=True, default='')
    vigencia = models.CharField(max_length=255, blank=True, default='')
    condiciones_pago = models.TextField(blank=True, default='')
    mostrar_clave = models.BooleanField(default=True)
    mostrar_precio_lista = models.BooleanField(default=True)
    mostrar_precio_descuento = models.BooleanField(default=True)
    mostrar_logistica = models.BooleanField(default=True)
    mostrar_descuento_total = models.BooleanField(default=True)
    
    # Campos de sistema
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_creadas'
    )
    usuario_envio = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_enviadas'
    )
    usuario_aprobacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_aprobadas'
    )
    usuario_rechazo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_rechazadas'
    )
    odoo_so = models.CharField(max_length=50, blank=True, null=True, help_text="Número de orden de venta en Odoo")
    hs_deal_id = models.CharField(max_length=50, blank=True, null=True, help_text="ID del negocio en HubSpot")
    subtotal_mobiliario = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    total_descuento = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    logistica = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    iva = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    total_general = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.folio} - {self.cliente}"

class Kit(models.Model):
    """
    Modelo que representa un kit de productos con sus valores calculados.
    Un kit es un conjunto de productos que se venden como una unidad.
    """
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(max_length=2048, blank=True, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)  # Campo para almacenar etiquetas
    cantidad = models.IntegerField(default=1, help_text='Cantidad de unidades del kit')
    valor_unitario = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    costo_unitario = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    porcentaje_descuento = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    valor_unitario_con_descuento = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='kits_creados'
    )

    class Meta:
        verbose_name = 'Kit'
        verbose_name_plural = 'Kits'

    def __str__(self):
        return f"{self.nombre}"
        
    def agregar_producto(self, clave, cantidad=1, porcentaje_descuento=0, **kwargs):
        """
        Agrega un producto al kit
        """
        producto = KitProducto.objects.create(
            kit=self,
            clave=clave,
            cantidad=cantidad,
            porcentaje_descuento=porcentaje_descuento,
            **kwargs
        )
        return producto
        
    def actualizar_producto(self, producto_kit_id, cantidad=None, porcentaje_descuento=None, **kwargs):
        """
        Actualiza un producto existente en el kit
        """
        try:
            producto = self.productos.get(id=producto_kit_id)
            
            if cantidad is not None:
                producto.cantidad = cantidad
                
            if porcentaje_descuento is not None:
                producto.porcentaje_descuento = porcentaje_descuento
                
            for key, value in kwargs.items():
                setattr(producto, key, value)
                
            producto.save()
            return producto
        except KitProducto.DoesNotExist:
            return None
            
    def eliminar_producto(self, producto_kit_id):
        """
        Elimina un producto del kit
        """
        try:
            producto = self.productos.get(id=producto_kit_id)
            producto.delete()
            return True
        except KitProducto.DoesNotExist:
            return False
            
    def duplicar(self, nuevo_nombre=None):
        """
        Crea una copia del kit actual con todos sus productos.
        
        Args:
            nuevo_nombre: Nombre opcional para el nuevo kit. Si no se proporciona,
                         se usará el nombre actual con '(Copia)' al final.
                         
        Returns:
            Kit: El nuevo kit creado.
        """
        nuevo_kit = Kit.objects.create(
            nombre=nuevo_nombre or f"{self.nombre} (Copia)",
            descripcion=self.descripcion,
            imagen_url=self.imagen_url,
            tag=self.tag,
            cantidad=self.cantidad,
            valor_unitario=self.valor_unitario,
            costo_unitario=self.costo_unitario,
            porcentaje_descuento=self.porcentaje_descuento,
            valor_unitario_con_descuento=self.valor_unitario_con_descuento,
            creado_por=self.creado_por
        )
        
        # Duplicar productos
        for producto in self.productos.all():
            KitProducto.objects.create(
                kit=nuevo_kit,
                clave=producto.clave,
                cantidad=producto.cantidad,
                porcentaje_descuento=producto.porcentaje_descuento,
                precio_lista=producto.precio_lista,
                costo=producto.costo,
                precio_descuento=producto.precio_descuento,
                importe=producto.importe,
                mostrar_en_kit=producto.mostrar_en_kit,
                descripcion=producto.descripcion,
                linea=producto.linea,
                familia=producto.familia,
                grupo=producto.grupo,
                producto_id=producto.producto_id
            )
        
        return nuevo_kit

class KitProducto(models.Model):
    """Modelo que representa la relación entre un Kit y un producto.
    Almacena la información necesaria para calcular precios y cantidades.
    """
    id = models.AutoField(primary_key=True)
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name='productos')
    clave = models.CharField(max_length=50, db_index=True)  
    cantidad = models.IntegerField(default=1)
    porcentaje_descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_lista = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Campo adicional para ordenar productos dentro del kit
    orden = models.IntegerField(default=0)
    
    # Nuevos campos
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    linea = models.CharField(max_length=100, blank=True, null=True)
    familia = models.CharField(max_length=100, blank=True, null=True)
    grupo = models.CharField(max_length=100, blank=True, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)  # Campo para almacenar etiquetas
    mostrar_en_kit = models.BooleanField(default=True)
    es_opcional = models.BooleanField(default=False)
    especial = models.BooleanField(default=False)  # Indica si es un producto especial
    padre = models.BooleanField(null=True, blank=True)  # Indica si es un producto padre, se establece según lo que envíe el usuario
    producto_id = models.IntegerField(blank=True, null=True)
    route_id = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Producto de Kit'
        verbose_name_plural = 'Productos de Kit'
        ordering = ['orden', 'id']
        unique_together = ('kit', 'clave')  # Evita duplicados del mismo producto en un kit
    
    def __str__(self):
        return f"{self.kit.nombre} - {self.clave} (x{self.cantidad})"

    def save(self, *args, **kwargs):
        """
        Sobrescribes el método save para calcular el precio con descuento y el importe
        """
        # Calcular precio con descuento
        if self.porcentaje_descuento > 0:
            self.precio_descuento = self.precio_lista * (1 - (self.porcentaje_descuento / 100))
        else:
            self.precio_descuento = self.precio_lista
        
        # Calcular importe
        self.importe = self.precio_descuento * self.cantidad
        
        super().save(*args, **kwargs)
        
        # Actualizar totales del kit
        self.kit.save()
        
    def get_producto_nombre(self):
        """
        Obtiene el nombre del producto desde ProductsCache
        """
        from .cache.models import ProductsCache
        try:
            # Intentar obtener el producto desde la tabla products_cache
            producto = ProductsCache.objects.get(reference_mask=self.clave)
            return producto.name
        except Exception:
            # Si hay cualquier error, devolver el reference_mask
            return self.clave
            
    def get_producto_imagen(self):
        """
        Obtiene la URL de la primera imagen del producto
        """
        from .cache.models import ProductsCache
        try:
            # Primero intentar obtener la imagen desde CotizadorImagenproducto
            # ya que es más probable que tenga la imagen más actualizada
            imagen = CotizadorImagenproducto.objects.filter(clave_padre=self.clave).first()
            if imagen and imagen.url:
                # No necesitamos codificar/decodificar ya que guardamos la URL con espacios ya codificados
                return imagen.url
                
            # Si no hay imagen en CotizadorImagenproducto, intentar con ProductsCache
            try:
                producto = ProductsCache.objects.get(reference_mask=self.clave)
                if producto.image_url:
                    return producto.image_url
            except Exception:
                pass
                
            return None
        except Exception:
            return None

class ProductoCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        'Cotizacion',
        on_delete=models.CASCADE,
        related_name='productos',
        db_column='cotizacion_uuid'  # Esta columna es en realidad bigint en la DB
    )
    es_kit = models.BooleanField(default=False)
    especial = models.BooleanField(default=False)
    padre = models.BooleanField(default=False)
    clave = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)  # Cambiado de CharField a TextField para permitir descripciones largas
    imagen_url = models.URLField(max_length=2048, blank=True, null=True)
    linea = models.CharField(max_length=100, blank=True, null=True)
    familia = models.CharField(max_length=100, blank=True, null=True)
    grupo = models.CharField(max_length=100, blank=True, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Campos numéricos
    cantidad = models.IntegerField(default=0)
    porcentaje_descuento = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    precio_lista = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    costo = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    precio_descuento = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    margen = models.IntegerField(default=0)
    importe = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    
    # Campos para kits
    kit_uuid = models.UUIDField(blank=True, null=True, db_index=True)
    kit_padre_id = models.IntegerField(blank=True, null=True)
    mostrar_en_cotizacion = models.BooleanField(default=True)
    
    producto_id = models.IntegerField(blank=True, null=True)
    route_id = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Producto de Cotización'
        verbose_name_plural = 'Productos de Cotización'

    def __str__(self):
        return f"{self.clave} - {self.descripcion}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribes el método save para asegurar que los valores numéricos
        se guarden correctamente y no sean None o cadenas vacías
        """
        # Asegurar que los campos numéricos tengan valores válidos
        if self.precio_lista is None:
            self.precio_lista = Decimal('0')
        if self.costo is None:
            self.costo = Decimal('0')
        if self.precio_descuento is None:
            self.precio_descuento = Decimal('0')
        if self.importe is None:
            self.importe = Decimal('0')
            
        # Solo recalcular el importe si no tiene un valor o es cero
        # Esto permite establecer el importe manualmente en otros lugares del código
        if (self.importe is None or self.importe == Decimal('0')) and self.precio_descuento and self.cantidad:
            self.importe = self.precio_descuento * self.cantidad
            
        super().save(*args, **kwargs)

class CotizadorImagenproducto(models.Model):
    """
    Modelo para almacenar las imágenes de los productos.
    Cada imagen está asociada a un producto mediante la clave_padre que coincide
    con el reference_mask de ProductTemplate.
    """
    id = models.BigAutoField(primary_key=True)
    clave_padre = models.CharField(
        max_length=255, 
        db_index=True,
        unique=True,
        help_text='Clave del producto que coincide con reference_mask de ProductTemplate'
    )
    url = models.CharField(
        max_length=2048,
        help_text='URL de la imagen en Supabase Storage'
    )

    class Meta:
        managed = True
        db_table = 'cotizador_imagenproducto'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        indexes = [
            models.Index(fields=['clave_padre'], name='idx_clave_padre'),
            models.Index(fields=['clave_padre', 'url'], name='idx_clave_url')
        ]

    def __str__(self):
        return f"Imagen de {self.clave_padre}"

    def get_product_template(self):
        """
        Obtiene el ProductTemplate asociado a esta imagen usando el reference_mask
        """
        return ProductTemplate.objects.using('erp-portalgebesa-com').filter(
            reference_mask=self.clave_padre,
            active=True,
            is_line=True
        ).first()

    def get_product_info(self):
        """
        Obtiene información detallada del producto asociado
        """
        product = self.get_product_template()
        if product:
            return {
                'id': product.id,
                'reference_mask': product.reference_mask,
                'description': product.description_picking,
                'type': product.type_id.name if product.type_id else None,
                'family': product.family_id.name if product.family_id else None,
                'line': product.line_id.name if product.line_id else None,
                'group': product.group_id.name if product.group_id else None
            }
        return None
