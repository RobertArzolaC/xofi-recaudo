import logging
from typing import Dict, Optional

from django.conf import settings
from heyoo import WhatsApp

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages via Meta's Cloud API."""

    def __init__(self):
        """Initialize WhatsApp service with credentials from settings."""
        self.token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.messenger = None

        if self.token and self.phone_number_id:
            try:
                self.messenger = WhatsApp(
                    token=self.token, phone_number_id=self.phone_number_id
                )
            except Exception as e:
                logger.error(f"Failed to initialize WhatsApp messenger: {e}")
        else:
            logger.warning(
                "WhatsApp credentials not configured. "
                "Please set WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID"
            )

    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return self.messenger is not None

    def send_text_message(
        self, recipient_phone: str, message: str
    ) -> Dict[str, any]:
        """
        Send a text message to a WhatsApp recipient.

        Args:
            recipient_phone: Phone number in international format (e.g., 51987654321)
            message: Text message to send

        Returns:
            dict: Response from WhatsApp API containing message ID and status
        """
        if not self.is_configured():
            raise ValueError("WhatsApp service is not configured")

        # Clean phone number (remove spaces, dashes, plus sign)
        clean_phone = self._clean_phone_number(recipient_phone)

        try:
            response = self.messenger.send_message(
                message=message, recipient_id=clean_phone
            )
            logger.info(f"Message sent to {clean_phone}: {response}")
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(f"Failed to send message to {clean_phone}: {e}")
            return {"success": False, "error": str(e)}

    def send_template_message(
        self,
        recipient_phone: str,
        template_name: str,
        language: str = "es",
        components: Optional[list] = None,
    ) -> Dict[str, any]:
        """
        Send a template message to a WhatsApp recipient.

        Args:
            recipient_phone: Phone number in international format
            template_name: Name of the approved WhatsApp template
            language: Language code (default: 'es' for Spanish)
            components: List of components for template variables

        Returns:
            dict: Response from WhatsApp API
        """
        if not self.is_configured():
            raise ValueError("WhatsApp service is not configured")

        clean_phone = self._clean_phone_number(recipient_phone)

        try:
            response = self.messenger.send_template(
                template=template_name,
                recipient_id=clean_phone,
                lang=language,
                components=components or [],
            )
            logger.info(
                f"Template message '{template_name}' sent to {clean_phone}: {response}"
            )
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(
                f"Failed to send template message to {clean_phone}: {e}"
            )
            return {"success": False, "error": str(e)}

    def send_message_with_button(
        self,
        recipient_phone: str,
        message: str,
        button_text: str,
        button_url: str,
    ) -> Dict[str, any]:
        """
        Send a message with a URL button (for payment links).

        Args:
            recipient_phone: Phone number in international format
            message: Text message to send
            button_text: Text to display on the button
            button_url: URL to open when button is clicked

        Returns:
            dict: Response from WhatsApp API
        """
        if not self.is_configured():
            raise ValueError("WhatsApp service is not configured")

        clean_phone = self._clean_phone_number(recipient_phone)

        try:
            # Create button payload
            button_payload = {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "payment_link",
                                "title": button_text,
                            },
                        }
                    ]
                },
            }

            # Note: For URL buttons, we need to use interactive messages
            # This requires a template with URL button or interactive message
            # For now, we'll send the message with the URL in the text
            full_message = f"{message}\n\n{button_text}: {button_url}"

            response = self.messenger.send_message(
                message=full_message, recipient_id=clean_phone
            )
            logger.info(
                f"Message with button sent to {clean_phone}: {response}"
            )
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(
                f"Failed to send message with button to {clean_phone}: {e}"
            )
            return {"success": False, "error": str(e)}

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

        # Ensure it starts with country code
        if len(clean) == 9:  # Peruvian number without country code
            clean = f"51{clean}"

        return clean

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
