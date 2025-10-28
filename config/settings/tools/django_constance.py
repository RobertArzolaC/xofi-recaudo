from django.utils.translation import gettext_lazy as _

# Django Constance
# https://django-constance.readthedocs.io/en/latest/

CONSTANCE_FILE_ROOT = "constance"

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_ADDITIONAL_FIELDS = {
    "image_field": ["django.forms.ImageField", {}],
    "json_field": ["django.forms.JSONField", {}],
}

CONSTANCE_CONFIG = {
    "PROJECT_NAME": ("Project Name", _("Project name.")),
    "COMPANY_LOGO": ("default.png", _("Company logo"), "image_field"),
    "COMPANY_DOMAIN": ("https://company.com/", _("Website domain.")),
    "JSON_FIELD_EXAMPLE": (
        {"name": "test"},
        _("Test json field"),
        "json_field",
    ),
    "ENABLE_SEND_EMAIL": (True, _("Enable sending emails.")),
    "ENABLE_VERIFICATION_EMAIL": (True, _("Enable email verification.")),
    "ITEMS_PER_PAGE": (
        4,
        _("Number of items to display per page in list views."),
    ),
    "CONTRIBUTION_AMOUNT": (
        100.00,
        _("Monthly contribution amount"),
        "decimal_field",
    ),
    "SOCIAL_SECURITY_AMOUNT": (
        50.00,
        _("Monthly social security amount"),
        "decimal_field",
    ),
    "CONTRIBUTION_DUE_DAY": (
        15,
        _("Day of the month for contribution payment (1-31)."),
    ),
    "SOCIAL_SECURITY_DUE_DAY": (
        15,
        _("Day of the month for social security payment (1-31)."),
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "1. General Options": {
        "fields": (
            "PROJECT_NAME",
            "COMPANY_LOGO",
            "JSON_FIELD_EXAMPLE",
            "COMPANY_DOMAIN",
            "ENABLE_SEND_EMAIL",
            "ENABLE_VERIFICATION_EMAIL",
            "ITEMS_PER_PAGE",
        ),
        "collapse": False,
    },
    "2. Compliance Settings": {
        "fields": (
            "CONTRIBUTION_AMOUNT",
            "SOCIAL_SECURITY_AMOUNT",
            "CONTRIBUTION_DUE_DAY",
            "SOCIAL_SECURITY_DUE_DAY",
            "ENABLE_CONTRIBUTION_CREATION",
            "ENABLE_SOCIAL_SECURITY_CREATION",
        ),
        "collapse": False,
    },
}
