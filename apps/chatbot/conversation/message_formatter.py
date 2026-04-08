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
            total_credits=summary.get("total_credits", 0),
            active_credits_count=summary.get("active_credits_count", 0),
            total_disbursed=summary.get("total_disbursed", 0),
            total_payments=summary.get("total_payments", 0),
            total_outstanding=summary.get("total_outstanding", 0),
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
                credit_id=credit["id"],
                product_name=credit["product"]["name"],
                amount=credit["amount"],
                outstanding_balance=credit["outstanding_balance"],
                status=credit["status"],
            )
        return result

    @staticmethod
    def format_credit_detail(credit_data: Dict) -> str:
        """Format detailed credit information."""
        credit = credit_data.get("credit", {})
        summary = credit_data.get("summary", {})

        return constants.CREDIT_DETAIL_TEMPLATE.format(
            credit_id=credit["id"],
            product_name=credit["product"]["name"],
            amount=credit["amount"],
            interest_rate=credit["interest_rate"],
            term_duration=credit["term_duration"],
            payment_amount=credit.get("payment_amount", 0),
            outstanding_balance=credit["outstanding_balance"],
            total_installments=summary.get("total_installments", 0),
            paid_installments=summary.get("paid_installments", 0),
            pending_installments=summary.get("pending_installments", 0),
            overdue_installments=summary.get("overdue_installments", 0),
        )

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
