class XofiErpRouter:
    """
    A router to control all database operations on models in
    the xofi-erp application.
    """

    route_app_labels = {
        "customers",
        "users",
        "compliance",
        "partners",
        "payments",
        "team",
        "credits",
        "campaigns",
        "support",
        "authtoken",
        "admin",
        "contenttypes",
        "ai_agent",
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "xofi-erp"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "xofi-erp"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == "xofi-erp"
        return db == "default"
