import logging
import time
from typing import Dict

import requests
from django.conf import settings

from apps.notifications.providers.base import BaseProvider
from apps.notifications.services.whatsapp_rate_limiter import WhatsAppRateLimiter

logger = logging.getLogger(__name__)


class WHAPIProvider(BaseProvider):
    """WhatsApp provider using WHAPI.cloud service."""

    def __init__(self):
        """Initialize WHAPI provider."""
        super().__init__()
        self.api_token = getattr(settings, "WHAPI_API_TOKEN", None)
        self.api_url = getattr(
            settings, "WHAPI_API_URL", "https://gate.whapi.cloud"
        )
        self.headers = None

        if self.api_token:
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        else:
            self.logger.warning(
                "WHAPI not configured. Set WHAPI_API_TOKEN in settings"
            )

    def is_configured(self) -> bool:
        """Check if WHAPI is properly configured."""
        return self.api_token is not None

    def send_text_message(
        self, recipient: str, message: str, **kwargs
    ) -> Dict[str, any]:
        """
        Send a text message via WHAPI with rate limiting and human-like behavior.

        Implements WHAPI best practices:
        - Typing indicator before sending
        - Random delays between messages
        - Rate limiting (6-12 messages/minute)

        Args:
            recipient: Phone number in international format
            message: Text message to send
            **kwargs: Additional parameters

        Returns:
            dict: Response with success status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHAPI provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient phone number"}

        try:
            clean_phone = self._clean_phone_number(recipient)

            # Apply typing indicator for human-like behavior
            self._send_typing_indicator(clean_phone)

            # Random delay to simulate human typing (5-10 seconds)
            delay = WhatsAppRateLimiter.get_random_delay()
            time.sleep(delay)

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

            # Record message sent for rate limiting
            WhatsAppRateLimiter.record_message_sent()

            self.logger.info(
                f"Message sent to {clean_phone} via WHAPI: {result}"
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            return self.handle_error(recipient, e)
        except Exception as e:
            return self.handle_error(recipient, e)

    def send_message_with_button(
        self,
        recipient: str,
        message: str,
        button_text: str,
        button_url: str,
        **kwargs,
    ) -> Dict[str, any]:
        """
        Send a message with a URL button via WHAPI with rate limiting.

        WHAPI supports interactive messages with buttons.
        Implements best practices for human-like behavior.

        Args:
            recipient: Phone number in international format
            message: Text message to send
            button_text: Text for the button
            button_url: URL for the button (will be converted to HTTPS)
            **kwargs: Additional parameters

        Returns:
            dict: Response with success status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WHAPI provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient phone number"}

        try:
            clean_phone = self._clean_phone_number(recipient)

            # Ensure HTTPS link (WHAPI recommendation)
            if button_url.startswith("http://"):
                button_url = button_url.replace("http://", "https://", 1)
                self.logger.warning(f"Converted HTTP link to HTTPS: {button_url}")

            # Apply typing indicator for human-like behavior
            self._send_typing_indicator(clean_phone)

            # Random delay to simulate human typing (5-10 seconds)
            delay = WhatsAppRateLimiter.get_random_delay()
            time.sleep(delay)

            # WHAPI supports interactive messages with buttons
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

            # Record message sent for rate limiting
            WhatsAppRateLimiter.record_message_sent()

            self.logger.info(
                f"Message with button sent to {clean_phone} via WHAPI: {result}"
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            return self.handle_error(recipient, e)
        except Exception as e:
            return self.handle_error(recipient, e)

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
        if len(clean) == 9:
            clean = f"51{clean}"

        # WHAPI format
        return f"{clean}@s.whatsapp.net"

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format."""
        if not super().validate_recipient(recipient):
            return False

        clean_phone = "".join(filter(str.isdigit, recipient))
        return len(clean_phone) >= 9

    def get_provider_info(self) -> Dict[str, any]:
        """Get WHAPI provider information."""
        return {
            "name": "WHAPI.cloud",
            "configured": self.is_configured(),
            "supports_buttons": True,
            "supports_templates": False,
            "rate_limit_status": WhatsAppRateLimiter.get_rate_limit_status(),
        }

    def _send_typing_indicator(self, recipient: str) -> None:
        """
        Send typing indicator to simulate human behavior.

        WHAPI recommendation: "Use 'typing...' or 'recording audio...' indicators"

        Args:
            recipient: Formatted phone number
        """
        try:
            payload = {"to": recipient, "state": "typing"}

            response = requests.post(
                f"{self.api_url}/messages/presence",
                json=payload,
                headers=self.headers,
                timeout=10,
            )

            if response.status_code == 200:
                self.logger.debug(f"Typing indicator sent to {recipient}")
            else:
                self.logger.warning(
                    f"Failed to send typing indicator: {response.status_code}"
                )
        except Exception as e:
            # Don't fail the whole message if typing indicator fails
            self.logger.warning(f"Error sending typing indicator: {e}")
