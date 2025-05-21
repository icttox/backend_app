from django.contrib import admin
from django.utils.html import format_html
from .models import ProductsCache

# Filtro personalizado para productos sin imágenes
class SinImagenFilter(admin.SimpleListFilter):
    title = 'Estado de imagen'
    parameter_name = 'tiene_imagen'

    def lookups(self, request, model_admin):
        return (
            ('sin_imagen', 'Sin imagen'),
            ('con_imagen', 'Con imagen'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'sin_imagen':
            return queryset.filter(image_url__isnull=True) | queryset.filter(image_url='')
        if self.value() == 'con_imagen':
            return queryset.exclude(image_url__isnull=True).exclude(image_url='')

@admin.register(ProductsCache)
class ProductsCacheAdmin(admin.ModelAdmin):
    list_display = [
        'reference_mask',
        'name',
        'get_image_preview',
        'type_name',
        'family_name',
        'line_name',
        'group_name',
        'is_line',
        'active',
        'last_sync'
    ]
    
    list_filter = [
        'active',
        'is_line',
        'type_name',
        'family_name',
        'line_name',
        'group_name',
        SinImagenFilter,  # Agregamos nuestro filtro personalizado
    ]
    
    search_fields = [
        'reference_mask',
        'name',
        'default_code',
        'description_sale'
    ]
    
    readonly_fields = [
        'id',
        'reference_mask',
        'name',
        'type_id',
        'family_id',
        'line_id',
        'group_id',
        'type_name',
        'family_name',
        'line_name',
        'group_name',
        'is_line',
        'active',
        'description_sale',
        'default_code',
        'image_url',
        'last_sync',
        'get_image_preview',
        'get_full_image'
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': ('reference_mask', 'name', 'default_code')
        }),
        ('Jerarquía', {
            'fields': (
                ('type_name', 'type_id'),
                ('family_name', 'family_id'),
                ('line_name', 'line_id'),
                ('group_name', 'group_id')
            )
        }),
        ('Estado', {
            'fields': ('is_line', 'active', 'last_sync')
        }),
        ('Descripción', {
            'fields': ('description_sale',)
        }),
        ('Imagen', {
            'fields': ('image_url', 'get_full_image')
        }),
    )
    
    ordering = ['name']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_image_preview(self, obj):
        """Vista previa pequeña para la lista"""
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image_url)
        return '-'
    get_image_preview.short_description = 'Vista Previa'
    get_image_preview.allow_tags = True

    def get_full_image(self, obj):
        """Imagen completa para el detalle"""
        if obj.image_url:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 100%; max-height: 400px;" />'
                '<br><a href="{}" target="_blank">Ver imagen completa</a>'
                '</div>',
                obj.image_url, obj.image_url
            )
        return 'No hay imagen disponible'
    get_full_image.short_description = 'Imagen del Producto'
    get_full_image.allow_tags = True
