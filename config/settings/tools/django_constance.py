from django.utils.translation import gettext_lazy as _

# Django Constance
# https://django-constance.readthedocs.io/en/latest/

CONSTANCE_FILE_ROOT = "constance"

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_ADDITIONAL_FIELDS = {
    "image_field": ["django.forms.ImageField", {}],
    "json_field": ["django.forms.JSONField", {}],
    "decimal_field": [
        "django.forms.DecimalField",
        {
            "max_digits": 10,
            "decimal_places": 2,
            "min_value": 0.00,
        },
    ],
}

CONSTANCE_CONFIG = {
    "PROJECT_NAME": ("Project Name", _("Project name.")),
    "COMPANY_LOGO_WHITE": ("default.png", _("Company logo"), "image_field"),
    "COMPANY_LOGO_BLACK": ("default.png", _("Company logo"), "image_field"),
    "COMPANY_DOMAIN": ("https://company.com/", _("Website domain.")),
    "COMPANY_PHONE": ("+51 999 999 999", _("Company contact phone.")),
    "ENABLE_SEND_EMAIL": (True, _("Enable sending emails.")),
    "ENABLE_VERIFICATION_EMAIL": (True, _("Enable email verification.")),
    "ENABLE_TELEGRAM_CHANEL": (
        False,
        _("Enable Telegram channel notifications."),
    ),
    "ENABLE_PAYMENT_LINKS": (True, _("Enable payment links in notifications.")),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "1. General Options": {
        "fields": (
            "PROJECT_NAME",
            "COMPANY_LOGO_WHITE",
            "COMPANY_LOGO_BLACK",
            "COMPANY_DOMAIN",
            "COMPANY_PHONE",
        ),
        "collapse": False,
    },
    "2. General Features": {
        "fields": (
            "ENABLE_SEND_EMAIL",
            "ENABLE_VERIFICATION_EMAIL",
            "ENABLE_PAYMENT_LINKS",
        ),
        "collapse": False,
    },
    "3. Campaign Settings": {
        "fields": ("ENABLE_TELEGRAM_CHANEL",),
        "collapse": True,
    },
}
