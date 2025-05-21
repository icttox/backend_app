from django.db import models
from django.utils.html import mark_safe

class ProductsCache(models.Model):
    """
    Modelo que representa la tabla de productos en Supabase.
    Esta tabla es una caché de los productos de PostgreSQL.
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    reference_mask = models.CharField(max_length=255)
    type_id = models.IntegerField(null=True)
    family_id = models.IntegerField(null=True)
    line_id = models.IntegerField(null=True)
    group_id = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    is_line = models.BooleanField(default=True)
    description_sale = models.TextField(null=True)
    default_code = models.CharField(max_length=64, null=True)
    type_name = models.CharField(max_length=255, null=True)
    family_name = models.CharField(max_length=255, null=True)
    line_name = models.CharField(max_length=255, null=True)
    group_name = models.CharField(max_length=255, null=True)
    image_url = models.URLField(max_length=512, null=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Django no manejará la creación/modificación de la tabla
        db_table = 'products_cache'  # Nombre de la tabla en Supabase
        app_label = 'cotizador'
        verbose_name = "Producto Supabase"
        verbose_name_plural = "Productos Supabase"

    def __str__(self):
        return f"{self.reference_mask} - {self.name}"

    def get_image_preview(self):
        """
        Retorna el HTML para mostrar la vista previa de la imagen
        """
        if self.image_url:
            return mark_safe(f'<img src="{self.image_url}" style="max-height: 50px;" />')
        return '-'