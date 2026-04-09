from typing import Dict, List, Optional

from constance import config
from django.conf import settings

from apps.chatbot import constants
from apps.core.utils.urls import get_absolute_url


class MessageFormatter:
    """Helper class to format messages for Telegram and WhatsApp."""

    @staticmethod
    def format_partner_info(partner_data: Dict) -> str:
        """Format partner information for display."""
        return constants.PARTNER_INFO_TEMPLATE.format(
            full_name=partner_data.get("full_name", "N/A"),
            document_number=partner_data.get("document_number", "N/A"),
            phone=partner_data.get("phone", "N/A"),
            email=partner_data.get("email", "N/A"),
        )

    @staticmethod
    def format_account_statement(summary_data: Dict) -> str:
        """Format account statement summary."""
        summary = summary_data.get("summary", {})
        return constants.ACCOUNT_STATEMENT_TEMPLATE.format(
            total_credits=summary.get("total_credits") or 0,
            active_credits_count=summary.get("active_credits_count") or 0,
            total_disbursed=summary.get("total_disbursed") or 0.0,
            total_payments=summary.get("total_payments") or 0.0,
            total_outstanding=summary.get("total_outstanding") or 0.0,
        )

    @staticmethod
    def format_credits_list(credits: List[Dict]) -> str:
        """Format list of credits."""
        if not credits:
            return constants.NO_CREDITS_MESSAGE

        result = constants.CREDIT_LIST_HEADER
        for i, credit in enumerate(credits, 1):
            result += constants.CREDIT_LIST_ITEM_TEMPLATE.format(
                index=i,
                credit_id=credit.get("id", ""),
                product_name=credit.get("product", {}).get("name", ""),
                amount=credit.get("amount") or 0.0,
                outstanding_balance=credit.get("outstanding_balance") or 0.0,
                status=credit.get("status", ""),
            )
        return result

    @staticmethod
    def format_credit_detail(credit_data: Dict) -> str:
        """Format detailed credit information."""
        credit = credit_data.get("credit", {})
        summary = credit_data.get("summary", {})

        return constants.CREDIT_DETAIL_TEMPLATE.format(
            credit_id=credit.get("id", ""),
            product_name=credit.get("product", {}).get("name", ""),
            amount=credit.get("amount") or 0.0,
            interest_rate=credit.get("interest_rate") or 0.0,
            term_duration=credit.get("term_duration") or 0,
            payment_amount=credit.get("payment_amount") or 0.0,
            outstanding_balance=credit.get("outstanding_balance") or 0.0,
            total_installments=summary.get("total_installments") or 0,
            paid_installments=summary.get("paid_installments") or 0,
            pending_installments=summary.get("pending_installments") or 0,
            overdue_installments=summary.get("overdue_installments") or 0,
        )

    @staticmethod
    def format_interactive_menu() -> dict:
        """
        Format the main interactive menu for WhatsApp (List Message).
        
        Returns:
            dict: Meta Interactive Message payload.
        """
        return {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Menú XoFi"
            },
            "body": {
                "text": "Elige una opción para continuar con tu consulta:"
            },
            "footer": {
                "text": "Asistente Virtual XoFi"
            },
            "action": {
                "button": "Ver opciones",
                "sections": [
                    {
                        "title": "📋 Consultas",
                        "rows": [
                            {
                                "id": "menu_perfil",
                                "title": "Mis datos personales",
                                "description": "Ver mi información registrada"
                            },
                            {
                                "id": "menu_estado_cuenta",
                                "title": "Estado de cuenta",
                                "description": "Ver resumen de créditos y saldos"
                            },
                            {
                                "id": "menu_prestamos",
                                "title": "Mis préstamos",
                                "description": "Ver lista de préstamos activos"
                            }
                        ]
                    },
                    {
                        "title": "🎫 Soporte",
                        "rows": [
                            {
                                "id": "menu_ticket",
                                "title": "Crear ticket",
                                "description": "Reportar un problema o consulta"
                            },
                            {
                                "id": "menu_comprobante",
                                "title": "Subir comprobante",
                                "description": "Registrar un pago realizado"
                            }
                        ]
                    }
                ]
            }
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
