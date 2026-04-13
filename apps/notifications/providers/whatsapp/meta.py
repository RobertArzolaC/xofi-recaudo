import logging
from typing import Dict, Optional

from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient
from apps.notifications.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class MetaWhatsAppProvider(BaseProvider):
    """WhatsApp provider using Meta's official Cloud API."""

    def __init__(self):
        """Initialize Meta WhatsApp provider."""
        super().__init__()
        try:
            self.client = WhatsAppCloudAPIClient()
        except Exception as e:
            self.logger.error(f"Failed to initialize Meta WhatsApp: {e}")
            self.client = None

    def is_configured(self) -> bool:
        """Check if Meta WhatsApp is properly configured."""
        if not self.client:
            return False
        return bool(self.client.api_key and self.client.phone_number_id)

    def send_text_message(
        self, recipient: str, message: str, **kwargs
    ) -> Dict[str, any]:
        """
        Send a text message via Meta WhatsApp.

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
                "error": "Meta WhatsApp provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient phone number"}

        try:
            clean_phone = self._clean_phone_number(recipient)
            response = self.client.send_message(
                to=clean_phone, message=message
            )
            self.logger.info(
                f"Message sent to {clean_phone} via Meta API: {response}"
            )
            return {
                "success": True,
                "response": response,
                "message_id": self.client._extract_message_id(response)
            }
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
        Send a message with a URL button via Meta WhatsApp.

        Note: Meta WhatsApp Cloud API has limitations with URL buttons.
        This implementation sends the message with the URL in the text.

        Args:
            recipient: Phone number in international format
            message: Text message to send
            button_text: Text for the button
            button_url: URL for the button
            **kwargs: Additional parameters

        Returns:
            dict: Response with success status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Meta WhatsApp provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient phone number"}

        try:
            clean_phone = self._clean_phone_number(recipient)

            # Meta Cloud API requires approved templates for buttons
            # For now, send as text with URL
            full_message = f"{message}\n\n{button_text}: {button_url}"

            response = self.client.send_message(
                to=clean_phone, message=full_message
            )
            self.logger.info(
                f"Message with button sent to {clean_phone} via Meta API: {response}"
            )
            return {
                "success": True,
                "response": response,
                "message_id": self.client._extract_message_id(response)
            }
        except Exception as e:
            return self.handle_error(recipient, e)

    def send_template_message(
        self,
        recipient: str,
        template_name: str,
        template_params: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, any]:
        """
        Send a pre-approved template message via Meta WhatsApp.

        Args:
            recipient: Phone number in international format
            template_name: Name of the approved template
            template_params: Parameters for the template (unused in favor of components)
            **kwargs: Additional parameters (language, components)

        Returns:
            dict: Response with success status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Meta WhatsApp provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient phone number"}

        try:
            clean_phone = self._clean_phone_number(recipient)
            language = kwargs.get("language", "es")
            components = kwargs.get("components", [])

            response = self.client.send_template(
                to=clean_phone,
                template_name=template_name,
                language=language,
                components=components,
            )
            self.logger.info(
                f"Template '{template_name}' sent to {clean_phone} via Meta API: {response}"
            )
            return {
                "success": True,
                "response": response,
                "message_id": self.client._extract_message_id(response)
            }
        except Exception as e:
            return self.handle_error(recipient, e)

    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and format phone number for WhatsApp API.

        Args:
            phone: Phone number in any format

        Returns:
            str: Clean phone number (digits only)
        """
        # Remove all non-digit characters
        clean = "".join(filter(str.isdigit, phone))

        # Add default country code if needed (e.g., Peru = 51)
        if len(clean) == 9:  # Assume local number
            clean = f"51{clean}"

        return clean

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format."""
        if not super().validate_recipient(recipient):
            return False

        clean_phone = "".join(filter(str.isdigit, recipient))
        return len(clean_phone) >= 9

    def get_provider_info(self) -> Dict[str, any]:
        """Get Meta WhatsApp provider information."""
        return {
            "name": "Meta WhatsApp Cloud API",
            "configured": self.is_configured(),
            "supports_buttons": False,  # Requires approved templates
            "supports_templates": True,
        }
