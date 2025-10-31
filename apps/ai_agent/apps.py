from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_agent'
    verbose_name = _("AI Agent")

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.ai_agent.signals  # noqa
        except ImportError:
            pass
