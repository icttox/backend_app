import os
from celery import Celery
from celery.schedules import crontab

# Establecer la configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_manager.settings')

app = Celery('app_manager')

# Usar la configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas automáticamente
app.autodiscover_tasks()

# Configurar tareas periódicas
app.conf.beat_schedule = {
    'sync-products-monday-8am': {
        'task': 'apps.cotizador.cache.tasks.sync_products_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=0),  # Lunes 8:00 AM
    },
}
