class DatabaseRouter:
    """
    Router para manejar las consultas a múltiples bases de datos.
    """
    def db_for_read(self, model, **hints):
        """
        Determina qué base de datos usar para lectura.
        """
        if model._meta.app_label == 'cotizador' and model.__name__ == 'ProductoOdoo':
            return 'odoo_db'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Todas las escrituras van a la base de datos default.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permite relaciones si ambos modelos están en la misma base de datos.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Asegura que las migraciones solo se apliquen a la base de datos default.
        """
        if db == 'odoo_db':
            return False
        return True


class ERPRouter:
    """
    Router para dirigir las consultas de modelos específicos a la base de datos ERP.
    """
    route_app_labels = {'cotizador'}
    erp_models = {'producttemplate', 'producttype', 'productfamily', 'productline', 'productgroup'}  

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels and model._meta.model_name in self.erp_models:
            return 'erp-portalgebesa-com'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels and model._meta.model_name in self.erp_models:
            return 'erp-portalgebesa-com'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels and model_name in self.erp_models:
            return False
        return None
