from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    ProductTemplate, Cotizacion, ProductoCotizacion, Producto, 
    ProductType, ProductFamily, ProductGroup, ProductLine, 
    CotizadorImagenproducto, Cliente
)
from django.utils.html import mark_safe

# Register your models here.

@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'reference_mask', 
        'name',
        'get_type', 
        'get_family', 
        'get_group', 
        'get_line',
        'preview_image'
    )
    search_fields = ('reference_mask', 'name')
    list_filter = ('type', 'family', 'line', 'group', 'is_line', 'active')
    list_select_related = ('type', 'family', 'line', 'group')
    readonly_fields = ('preview_image', 'image_gallery')

    def get_type(self, obj):
        return obj.type.name if obj.type else '-'
    get_type.short_description = 'Tipo'
    get_type.admin_order_field = 'type__name'

    def get_family(self, obj):
        return obj.family.name if obj.family else '-'
    get_family.short_description = 'Familia'
    get_family.admin_order_field = 'family__name'

    def get_group(self, obj):
        return obj.group.name if obj.group else '-'
    get_group.short_description = 'Grupo'
    get_group.admin_order_field = 'group__name'

    def get_line(self, obj):
        return obj.line.name if obj.line else '-'
    get_line.short_description = 'Línea'
    get_line.admin_order_field = 'line__name'

    def preview_image(self, obj):
        return obj.get_image_preview()
    preview_image.short_description = 'Imagen'
    preview_image.allow_tags = True

    def image_gallery(self, obj):
        return obj.get_image_gallery()
    image_gallery.short_description = 'Galería de Imágenes'
    image_gallery.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).using('erp-portalgebesa-com')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).using('erp-portalgebesa-com')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ProductFamily)
class ProductFamilyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).using('erp-portalgebesa-com')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).using('erp-portalgebesa-com')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).using('erp-portalgebesa-com')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_producto', 'precio_base', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo_producto', 'descripcion']
    ordering = ['codigo_producto']

@admin.register(ProductoCotizacion)
class ProductoCotizacionAdmin(admin.ModelAdmin):
    list_display = ['clave', 'descripcion', 'cantidad', 'precio_lista']
    search_fields = ['clave', 'descripcion']

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['folio', 'version', 'proyecto', 'cliente', 'vendedor', 'estatus']
    list_filter = ['estatus']
    search_fields = ['folio', 'proyecto', 'cliente', 'vendedor']
    readonly_fields = [
        'uuid',
        'folio',
        'version',
        'fecha_creacion',
        'fecha_modificacion'
    ]
    fieldsets = (
        ('Información de Control', {
            'fields': (
                'folio', 'version', 'estatus', 'motivo'
            )
        }),
        ('Información del Proyecto', {
            'fields': (
                'proyecto', 'fecha_proyecto', 'unidad_facturacion'
            )
        }),
        ('Información del Cliente', {
            'fields': (
                'cliente', 'persona_contacto', 'email_cliente', 'telefono_cliente'
            )
        }),
        ('Información del Vendedor', {
            'fields': (
                'vendedor', 'email_vendedor', 'telefono_vendedor', 'proyectista'
            )
        }),
        ('Configuración PDF', {
            'fields': (
                'tiempo_entrega', 'vigencia', 'condiciones_pago',
                'mostrar_clave', 'mostrar_precio_lista', 'mostrar_precio_descuento',
                'mostrar_logistica', 'mostrar_descuento_total'
            )
        }),
        ('Totales', {
            'fields': (
                'subtotal_mobiliario', 'logistica', 'iva', 'total_general'
            )
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion', 'fecha_modificacion'
            )
        })
    )

@admin.register(CotizadorImagenproducto)
class CotizadorImagenproductoAdmin(admin.ModelAdmin):
    list_display = [
        'clave_padre',
        'get_color',
        'mostrar_imagen',
        'get_es_principal'
    ]
    search_fields = ['clave_padre']

    def get_color(self, obj):
        return getattr(obj, 'get_color', '-')
    get_color.short_description = 'Color'

    def get_es_principal(self, obj):
        return getattr(obj, 'es_principal', False)
    get_es_principal.short_description = 'Es Principal'
    get_es_principal.boolean = True

    def mostrar_imagen(self, obj):
        if obj.url:
            return mark_safe(f'<img src="{obj.url}" style="max-height: 50px;" />')
        return '-'
    mostrar_imagen.short_description = 'Vista Previa'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('partner_id', 'name_partner', 'rfc')
    search_fields = ('name_partner', 'rfc')
    list_filter = ('partner_id',)
