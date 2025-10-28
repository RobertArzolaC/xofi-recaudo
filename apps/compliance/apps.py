from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ComplianceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compliance"
    verbose_name = _("Compliance")
