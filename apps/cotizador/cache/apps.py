from django.apps import AppConfig

class CacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cotizador.cache'
    verbose_name = 'Caché de Productos'
