from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the Notifications app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self):
        """Import tasks when app is ready to register them with Celery."""
        import apps.notifications.tasks  # noqa: F401
