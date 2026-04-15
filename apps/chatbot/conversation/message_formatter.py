from typing import Optional

from constance import config
from django.conf import settings

from apps.chatbot import constants
from apps.core.utils.urls import get_absolute_url


class MessageFormatter:
    """Helper class to format messages for Telegram and WhatsApp."""

    @staticmethod
    def format_interactive_menu() -> dict:
        """
        Format the main interactive menu for WhatsApp (List Message).

        Returns:
            dict: Meta Interactive Message payload.
        """
        return {
            "type": "list",
            "header": {"type": "text", "text": "Menú XoFi"},
            "body": {
                "text": "Elige una opción para continuar con tu consulta:"
            },
            "footer": {"text": "Asistente Virtual XoFi"},
            "action": {
                "button": "Ver opciones",
                "sections": [
                    {
                        "title": "📋 Consultas",
                        "rows": [
                            {
                                "id": "menu_perfil",
                                "title": "Mis datos personales",
                                "description": "Ver mi información registrada",
                            },
                            {
                                "id": "menu_estado_cuenta",
                                "title": "Estado de cuenta",
                                "description": "Ver resumen de créditos y saldos",
                            },
                            {
                                "id": "menu_prestamos",
                                "title": "Mis préstamos",
                                "description": "Ver lista de préstamos activos",
                            },
                        ],
                    },
                    {
                        "title": "🎫 Soporte",
                        "rows": [
                            {
                                "id": "menu_ticket",
                                "title": "Crear ticket",
                                "description": "Reportar un problema o consulta",
                            },
                            {
                                "id": "menu_comprobante",
                                "title": "Subir comprobante",
                                "description": "Registrar un pago realizado",
                            },
                        ],
                    },
                ],
            },
        }

    @staticmethod
    def format_help_message() -> str:
        """Format help message with available options."""
        return f"{config.CHATBOT_WELCOME_MESSAGE}\n{constants.MENU_MESSAGE}"

    @staticmethod
    def format_authentication_prompt() -> str:
        """Format authentication request message using constance configuration."""
        return constants.AUTHENTICATION_PROMPT

    @staticmethod
    def get_welcome_image() -> Optional[str]:
        """Get welcome image filename from constance configuration.

        Returns:
            str or None: Image filename if configured, None otherwise.
        """
        return config.CHATBOT_WELCOME_IMAGE or None

    @staticmethod
    def get_welcome_image_url() -> Optional[str]:
        """Get welcome image absolute URL from constance configuration.

        Constructs the full URL using COMPANY_DOMAIN and MEDIA_URL settings.

        Returns:
            str or None: Absolute URL for the welcome image if configured, None otherwise.
        """
        welcome_image = config.CHATBOT_WELCOME_IMAGE
        if not welcome_image:
            return None

        # Build absolute URL for the image
        media_url = settings.MEDIA_URL.strip("/")
        return get_absolute_url(f"/{media_url}/constance/{welcome_image}")

    @staticmethod
    def format_error_message(error: str) -> str:
        """Format error message."""
        return f"❌ *Error:* {error}"

    @staticmethod
    def format_success_message(message: str) -> str:
        """Format success message."""
        return f"✅ {message}"
