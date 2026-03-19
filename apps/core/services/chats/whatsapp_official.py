import logging
from typing import Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppOfficialService:
    """Service for sending WhatsApp messages via Meta's official Business Cloud API."""

    def __init__(self):
        self.access_token = getattr(settings, "WHATSAPP_API_TOKEN", None)
        self.phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)
        api_version = getattr(settings, "WHATSAPP_API_VERSION", "v21.0")
        self.graph_api_base = f"https://graph.facebook.com/{api_version}"

        if not self.access_token or not self.phone_number_id:
            logger.warning(
                "Meta WhatsApp Business API not configured. "
                "Set WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID in settings."
            )

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def _headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _url(self) -> str:
        return f"{self.graph_api_base}/{self.phone_number_id}/messages"

    def send_text_message(self, recipient_phone: str, message: str) -> Dict:
        """
        Send a plain text message via Meta WhatsApp Cloud API.

        Args:
            recipient_phone: Phone in international format (e.g. 51987654321)
            message: Text to send
        """
        if not self.is_configured():
            return {"success": False, "error": "WhatsApp API not configured"}

        try:
            clean_phone = self._clean_phone(recipient_phone)
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": "text",
                "text": {"preview_url": False, "body": message},
            }

            response = requests.post(
                self._url(), json=payload, headers=self._headers(), timeout=30
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Text sent to {clean_phone}: {result.get('messages', [{}])[0].get('id')}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id"), "response": result}

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send text to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending text to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}

    def send_image_message(
        self, recipient_phone: str, image_url: str, caption: Optional[str] = None
    ) -> Dict:
        """
        Send an image message via Meta WhatsApp Cloud API.

        Args:
            recipient_phone: Phone in international format
            image_url: Publicly accessible URL of the image
            caption: Optional caption text
        """
        if not self.is_configured():
            return {"success": False, "error": "WhatsApp API not configured"}

        try:
            clean_phone = self._clean_phone(recipient_phone)
            image_payload: Dict = {"link": image_url}
            if caption:
                image_payload["caption"] = caption

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": "image",
                "image": image_payload,
            }

            response = requests.post(
                self._url(), json=payload, headers=self._headers(), timeout=30
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Image sent to {clean_phone}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id"), "response": result}

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send image to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending image to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}

    def mark_as_read(self, message_id: str) -> Dict:
        """Mark a received message as read."""
        if not self.is_configured():
            return {"success": False, "error": "WhatsApp API not configured"}

        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            }
            response = requests.post(
                self._url(), json=payload, headers=self._headers(), timeout=10
            )
            response.raise_for_status()
            return {"success": True}
        except Exception as e:
            logger.warning(f"Could not mark message {message_id} as read: {e}")
            return {"success": False, "error": str(e)}

    def _clean_phone(self, phone: str) -> str:
        """
        Strip non-digits and ensure country code.
        Meta API expects plain international format: 51987654321
        """
        clean = "".join(filter(str.isdigit, phone))
        if len(clean) == 9:  # Peruvian number without country code
            clean = f"51{clean}"
        return clean
