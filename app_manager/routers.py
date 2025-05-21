class DatabaseRouter:
    """
    Router para manejar las consultas a múltiples bases de datos.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'cotizador' and model._meta.db_table == 'product_template':
            return 'erp-portalgebesa-com'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'cotizador' and model._meta.db_table == 'product_template':
            return None  # No permitir escrituras en la base de datos ERP
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'erp-portalgebesa-com':
            return False  # No realizar migraciones en la base de datos ERP
        return True
