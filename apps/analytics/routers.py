# Router para dirigir lecturas/escrituras de la app analytics al DB alias 'analytics'.
class AnalyticsRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'analytics':
            return 'analytics'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'analytics':
            return 'analytics'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if getattr(obj1._meta, 'app_label', None) == 'analytics' or getattr(obj2._meta, 'app_label', None) == 'analytics':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'analytics':
            return False
        return None
