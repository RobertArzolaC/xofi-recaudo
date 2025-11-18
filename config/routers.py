class XofiErpRouter:
    """
    A router to control all database operations on models in
    the xofi-erp application.
    """

    remote_app_labels = {
        # Apps principales del negocio
        "users",
        "customers",
        "compliance",
        "partners",
        "payments",
        "team",
        "credits",
        "campaigns",
        "notifications",
        "support",
        "chatbot",
        "reports",
        # Apps de terceros que manejan datos del negocio
        "cities_light",
        "constance",
        # Apps de auditoría
        "easyaudit",
        "admin",
        # Apps de autenticación relacionadas con usuarios
        "authtoken",
    }

    local_app_labels = {
        # Apps que deben estar en la DB principal
        "auth",
        "contenttypes",
        "sessions",
        "messages",
        "staticfiles",
        "django_celery_beat",
        "allauth",
        "account",
        "core",
        "authentication",
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.remote_app_labels:
            return "xofi-erp"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.remote_app_labels:
            return "xofi-erp"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.remote_app_labels
            or obj2._meta.app_label in self.remote_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.remote_app_labels:
            return db == "xofi-erp"
        elif app_label in self.local_app_labels:
            return db == "default"
        return None
