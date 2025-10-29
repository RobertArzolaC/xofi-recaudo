from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.campaigns"
    verbose_name = "Campaigns"

    def ready(self):
        """Import tasks to register them with Celery."""
        import apps.campaigns.tasks  # noqa: F401
