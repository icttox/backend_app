from django.contrib import admin
from .models import (
    Categoria,
    Almacen,
    PropuestaCompra,
    ItemPropuestaCompra
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('categoria_id', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('categoria_id', 'nombre', 'descripcion')
    ordering = ('nombre',)
    list_editable = ('activo', 'nombre')





# Almacenes desregistrados del admin porque son simplemente una caché de datos externos
# @admin.register(Almacen)
# class AlmacenAdmin(admin.ModelAdmin):
#     list_display = ('almacen_id', 'nombre', 'codigo', 'activo', 'ultima_actualizacion')
#     list_filter = ('activo',)
#     search_fields = ('almacen_id', 'nombre', 'codigo')
#     ordering = ('nombre',)
#     list_editable = ('activo', 'nombre', 'codigo')

class ItemPropuestaCompraInline(admin.TabularInline):
    model = ItemPropuestaCompra
    fk_name = 'propuesta'  # Especificar el campo de clave foránea
    extra = 0
    fields = ('categoria', 'codigo', 'producto', 'medida', 'registrar', 'produccion', 'cantidad_propuesta', 'proveedor', 'meses', 'comentarios')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    can_delete = True
    show_change_link = True

@admin.register(PropuestaCompra)
class PropuestaCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero', 'comprador', 'estado', 'fecha_creacion', 'fecha_envio')
    list_filter = ('estado', 'comprador', 'fecha_creacion', 'fecha_envio')
    search_fields = ('numero', 'comprador__usuario__email', 'comprador__nombre_comprador', 'comentarios')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_envio', 'fecha_aprobacion_rechazo')
    # Ya no usamos filter_horizontal porque almacenes_ids es un JSONField, no una relación ManyToMany
    raw_id_fields = ('comprador', 'usuario_aprobador')
    inlines = [ItemPropuestaCompraInline]
    fieldsets = (
        (None, {
            'fields': ('comprador', 'numero', 'estado', 'almacenes_ids')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_envio', 'fecha_aprobacion_rechazo')
        }),
        ('Aprobación', {
            'fields': ('usuario_aprobador', 'comentarios')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado != PropuestaCompra.ESTADO_BORRADOR:
            # Si no es un borrador, muchos campos deberían ser de solo lectura
            return self.readonly_fields + ('comprador', 'numero', 'estado', 'almacenes', 'usuario_aprobador')
        return self.readonly_fields

@admin.register(ItemPropuestaCompra)
class ItemPropuestaCompraAdmin(admin.ModelAdmin):
    list_display = ('propuesta', 'codigo', 'producto', 'cantidad_propuesta', 'registrar')
    list_filter = ('categoria',)
    search_fields = ('codigo', 'producto', 'categoria', 'propuesta__numero')
    readonly_fields = ('propuesta', 'fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Propuesta', {
            'fields': ('propuesta',)
        }),
        ('Información de Producto', {
            'fields': ('categoria', 'codigo', 'producto', 'medida')
        }),
        ('Cantidades', {
            'fields': ('registrar', 'produccion', 'cantidad_propuesta')
        }),
        ('Detalles Adicionales', {
            'fields': ('proveedor', 'meses', 'comentarios')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.propuesta.estado != PropuestaCompra.ESTADO_BORRADOR:
            # Si la propuesta no es un borrador, todo debe ser de solo lectura
            return self.readonly_fields + ('categoria', 'codigo', 'producto', 'medida', 'registrar', 'produccion', 'cantidad_propuesta', 'proveedor', 'meses', 'comentarios')
        return self.readonly_fields
