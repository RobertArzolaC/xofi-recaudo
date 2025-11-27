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
    "textarea_field": [
        "django.forms.CharField",
        {
            "widget": "django.forms.Textarea",
        },
    ],
}

# Default welcome message for chatbot
CHATBOT_WELCOME_MESSAGE_DEFAULT = """
🤖 *Bienvenido al Asistente Virtual de XoFi*

Soy tu asistente virtual y estoy aquí para ayudarte con:

📋 Consultas sobre tu cuenta y préstamos
💰 Estado de cuenta y pagos
🎫 Soporte técnico
📄 Carga de comprobantes

Para comenzar, necesito autenticarte.

Por favor, envía tu *número de documento* y *año de nacimiento* separados por un espacio.

*Ejemplo:* 12345678 1990
"""

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
    # Chatbot settings
    "CHATBOT_WELCOME_IMAGE": (
        "",
        _("Chatbot welcome image. Sent before welcome message on WhatsApp."),
        "image_field",
    ),
    "CHATBOT_WELCOME_MESSAGE": (
        CHATBOT_WELCOME_MESSAGE_DEFAULT,
        _("Chatbot welcome message displayed when user starts conversation."),
        "textarea_field",
    ),
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
    "4. Chatbot Settings": {
        "fields": (
            "CHATBOT_WELCOME_IMAGE",
            "CHATBOT_WELCOME_MESSAGE",
        ),
        "collapse": False,
    },
}
