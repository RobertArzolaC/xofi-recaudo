import logging
from typing import Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages via WHAPI.cloud."""

    def __init__(self):
        """Initialize WhatsApp service with WHAPI credentials from settings."""
        self.api_token = getattr(settings, "WHAPI_API_TOKEN", None)
        self.api_url = getattr(
            settings, "WHAPI_BASE_URL", "https://gate.whapi.cloud"
        )
        self.headers = None

        if self.api_token:
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            logger.info("WhatsApp service initialized with WHAPI")
        else:
            logger.warning(
                "WHAPI not configured. Set WHATSAPP_API_TOKEN in settings"
            )

    def is_configured(self) -> bool:
        """Check if WHAPI is properly configured."""
        return self.api_token is not None

    def send_text_message(
        self, recipient_phone: str, message: str
    ) -> Dict[str, any]:
        """
        Send a text message via WHAPI.

        Args:
            recipient_phone: Phone number in international format (e.g., 51987654321)
            message: Text message to send

        Returns:
            dict: Response from WHAPI containing message ID and status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHAPI provider is not configured",
            }

        try:
            clean_phone = self._clean_phone_number(recipient_phone)

            payload = {
                "to": clean_phone,
                "body": message,
            }

            response = requests.post(
                f"{self.api_url}/messages/text",
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Message sent to {clean_phone} via WHAPI: {result}")
            return {
                "success": True,
                "message_id": result.get("id"),
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(
                f"Unexpected error sending message to {recipient_phone}: {e}"
            )
            return {"success": False, "error": str(e)}

    def send_template_message(
        self,
        recipient_phone: str,
        template_name: str,
        language: str = "es",
        components: Optional[list] = None,
    ) -> Dict[str, any]:
        """
        Send a template message via WHAPI.

        Note: WHAPI supports templates but they need to be approved by WhatsApp first.
        For chatbot purposes, we typically use regular text messages instead.

        Args:
            recipient_phone: Phone number in international format
            template_name: Name of the approved WhatsApp template
            language: Language code (default: 'es' for Spanish)
            components: List of components for template variables

        Returns:
            dict: Response from WHAPI
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHAPI provider is not configured",
            }

        logger.warning(
            "Template messages not fully implemented for WHAPI. "
            "Using regular text message instead."
        )

        # For now, fall back to regular text message
        # In production, you would implement proper template support
        return self.send_text_message(
            recipient_phone,
            f"[Template: {template_name}] Please use regular messages for chatbot.",
        )

    def send_message_with_button(
        self,
        recipient_phone: str,
        message: str,
        button_text: str,
        button_url: str,
    ) -> Dict[str, any]:
        """
        Send a message with a URL button via WHAPI.

        WHAPI supports interactive messages with URL buttons.

        Args:
            recipient_phone: Phone number in international format
            message: Text message to send
            button_text: Text to display on the button
            button_url: URL to open when button is clicked

        Returns:
            dict: Response from WHAPI
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHAPI provider is not configured",
            }

        try:
            clean_phone = self._clean_phone_number(recipient_phone)

            # Ensure HTTPS link (WHAPI recommendation)
            if button_url.startswith("http://"):
                button_url = button_url.replace("http://", "https://", 1)
                logger.warning(f"Converted HTTP link to HTTPS: {button_url}")

            # WHAPI interactive message with URL button
            payload = {
                "to": clean_phone,
                "body": message,
                "footer": "",
                "buttons": [
                    {
                        "type": "url",
                        "title": button_text,
                        "url": button_url,
                    }
                ],
            }

            response = requests.post(
                f"{self.api_url}/messages/interactive",
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Message with button sent to {clean_phone} via WHAPI: {result}"
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to send message with button to {recipient_phone}: {e}"
            )
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(
                f"Unexpected error sending message with button to {recipient_phone}: {e}"
            )
            return {"success": False, "error": str(e)}

    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and format phone number for WHAPI.

        WHAPI expects format: <country_code><number>@s.whatsapp.net

        Args:
            phone: Phone number in any format

        Returns:
            str: Formatted phone number for WHAPI
        """
        # Remove all non-digit characters
        clean = "".join(filter(str.isdigit, phone))

        # Add default country code if needed
        if len(clean) == 9:  # Peruvian number without country code
            clean = f"51{clean}"

        # WHAPI format
        return f"{clean}@s.whatsapp.net"

    def get_message_status(self, message_id: str) -> Dict[str, any]:
        """
        Get the status of a sent message.

        Args:
            message_id: WhatsApp message ID

        Returns:
            dict: Message status information
        """
        # Note: Status updates are typically received via webhooks
        # This is a placeholder for future webhook implementation
        logger.info(f"Checking status for message: {message_id}")
        return {"message_id": message_id, "status": "unknown"}


# Singleton instance
whatsapp_service = WhatsAppService()
