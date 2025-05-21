from celery import shared_task
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from .sync import sync_products_to_supabase

logger = get_task_logger(__name__)

@shared_task
def sync_products_task():
    """
    Tarea Celery para sincronizar productos desde PostgreSQL a Supabase
    """
    try:
        result = sync_products_to_supabase()
        logger.info(f'Sincronización completada: {result}')
        return result
    except Exception as e:
        logger.error(f'Error en sincronización: {str(e)}')
        raise
