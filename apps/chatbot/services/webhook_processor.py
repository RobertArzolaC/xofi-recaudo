import logging
from typing import Dict, Optional

import requests
from decouple import config

from apps.chatbot import constants
from apps.chatbot.choices import MessageDeliveryStatus
from apps.chatbot.conversation import ConversationService
from apps.chatbot.models import ConversationMessage
from apps.chatbot.services.openrouter_ocr import OpenRouterOCRService
from apps.chatbot.services.partner_api import PartnerAPIService
from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient

logger = logging.getLogger(__name__)


class WhatsAppWebhookProcessor:
    """
    Encapsulates the logic for processing WhatsApp Webhooks.

    This class refactors functions previously found in tasks.py into a
    maintainable and scalable structure.
    """

    def __init__(self):
        self.client = WhatsAppCloudAPIClient()
        self.conv_service = ConversationService()
        self.ocr_service = OpenRouterOCRService()
        self.api_service = PartnerAPIService()

    def process(self, webhook_data: Dict) -> Dict:
        """Main entry point for processing the webhook payload."""
        if webhook_data.get("object") != "whatsapp_business_account":
            logger.warning(
                "Unexpected webhook object: %s", webhook_data.get("object")
            )
            return {"status": "ignored"}

        for entry in webhook_data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue

                value = change.get("value", {})

                # Process messages
                for message in value.get("messages", []):
                    self._process_single_message(message)

                # Process delivery statuses
                for status in value.get("statuses", []):
                    self._process_delivery_status(status)

        return {"status": "success"}

    def _process_single_message(self, message: Dict) -> None:
        """Determine message type and delegate to specialized handler."""
        sender_phone = message.get("from")
        message_type = message.get("type")
        message_id = message.get("id")

        logger.info(
            "Processing %s message from %s (id=%s)",
            message_type,
            sender_phone,
            message_id,
        )

        if message_id:
            try:
                self.client.mark_message_as_read(message_id)
            except Exception as exc:
                logger.warning(
                    "Could not mark message %s as read: %s", message_id, exc
                )

        handlers = {
            "text": self._handle_text,
            "image": self._handle_image,
            "interactive": self._handle_interactive,
        }

        handler = handlers.get(message_type)
        if handler:
            try:
                handler(message)
            except Exception as exc:
                logger.error(
                    "Error in handler %s: %s", message_type, exc, exc_info=True
                )
                self._send_text(
                    sender_phone, constants.ERROR_PROCESSING_MESSAGE
                )
        else:
            logger.warning("Unsupported message type: %s", message_type)
            self._send_text(
                sender_phone,
                "Lo siento, ese tipo de mensaje no es soportado. Por favor envía un mensaje de texto.",
            )

    def _handle_text(self, message: Dict) -> None:
        """Handle incoming text messages."""
        sender_phone = message.get("from")
        user_message = message.get("text", {}).get("body", "")

        conversation = self.conv_service.get_or_create_conversation_whatsapp(
            sender_phone
        )

        # Conversation service handles everything (auth interception, AI agent, etc.)
        response, _ = self.conv_service.process_message_whatsapp(
            sender_phone, user_message
        )

        wamid = self._send_response(sender_phone, response)

        if wamid:
            self._update_agent_message_id(conversation, wamid)

    def _handle_image(self, message: Dict) -> None:
        """Handle incoming image messages (OCR processing)."""
        logger.info(
            "Processing image message from %s (id=%s)",
            message.get("from"),
            message.get("id"),
        )
        sender_phone = message.get("from")
        image_data = message.get("image", {})
        caption = image_data.get("caption", "")
        media_id = image_data.get("id")

        conversation = self.conv_service.get_or_create_conversation_whatsapp(
            sender_phone
        )

        if not conversation.authenticated or not conversation.partner:
            self._send_text(
                sender_phone,
                "Por favor, autentícate primero enviando tu DNI y año de nacimiento.\n\nEjemplo: DNI 12345678 año 1990",
            )
            return

        image_bytes = self._download_media(media_id)
        if not image_bytes:
            self._send_text(
                sender_phone,
                "❌ No se pudo descargar la imagen. Intenta nuevamente.",
            )
            return

        # Use the new OpenRouter OCR Service
        extracted = self.ocr_service.extract_receipt_data(image_bytes)

        # Upload to backend API
        result = self.api_service.upload_payment_receipt(
            conversation.partner.id,
            image_bytes,
            f"receipt_{media_id}",
            extracted.get("amount"),
            extracted.get("date"),
            extracted.get("notes", ""),
        )

        if result and result.get("id"):
            msg = (
                f"✅ *Boleta recibida*\n\n"
                f"📝 ID: {extracted.get('document_id') or 'N/A'}\n"
                f"💰 Monto: S/ {result.get('amount')}\n"
                f"📅 Fecha: {result.get('payment_date')}\n\n"
                f"Será revisada por nuestro equipo."
            )
            wamid = self._send_text(sender_phone, msg)

            # Persist messages
            self.conv_service.save_message(
                conversation,
                "USER",
                f"[IMAGE] {caption}" if caption else "[IMAGE]",
                metadata={"receipt_id": result.get("id"), "media_id": media_id},
            )
            self.conv_service.save_message(
                conversation,
                "AGENT",
                msg,
                whatsapp_message_id=wamid,
                delivery_status=MessageDeliveryStatus.SENT if wamid else None,
            )
        else:
            self._send_text(
                sender_phone,
                "❌ Error al procesar tu boleta. Contacta con soporte.",
            )

    def _handle_interactive(self, message: Dict) -> None:
        """Handle interactive replies (buttons/lists)."""
        sender_phone = message.get("from")
        interactive = message.get("interactive", {})
        itype = interactive.get("type")

        reply_text = ""
        if itype == "button_reply":
            reply_text = interactive.get("button_reply", {}).get("title", "")
        elif itype == "list_reply":
            reply_text = interactive.get("list_reply", {}).get("title", "")

        if reply_text:
            # Re-inject as a text message
            self._handle_text(
                {"from": sender_phone, "text": {"body": reply_text}}
            )
        else:
            self._send_text(
                sender_phone,
                "Opción no reconocida. Por favor usa comandos de texto.",
            )

    def _process_delivery_status(self, status: Dict) -> None:
        """Update message delivery status in database."""
        message_id = status.get("id")
        status_value = status.get("status", "").upper()

        status_map = {
            "SENT": MessageDeliveryStatus.SENT,
            "DELIVERED": MessageDeliveryStatus.DELIVERED,
            "READ": MessageDeliveryStatus.READ,
            "FAILED": MessageDeliveryStatus.FAILED,
        }

        delivery_status = status_map.get(status_value)
        if message_id and delivery_status:
            ConversationMessage.objects.filter(
                whatsapp_message_id=message_id
            ).update(delivery_status=delivery_status)

    # ── Sending Helpers ───────────────────────────────────────────────

    def _send_response(self, phone: str, response) -> Optional[str]:
        """Sends a BotResponse object (text, interactive, or template)."""
        if getattr(response, "template", None):
            try:
                res = self.client.send_template(
                    to=phone,
                    template_name=response.template["name"],
                    language=response.template.get("language", "es_PE"),
                    components=response.template.get("components"),
                )
                return self.client._extract_message_id(res)
            except Exception as exc:
                logger.error("Failed to send template to %s: %s", phone, exc)
                return None

        if response.interactive:
            return self._send_interactive(phone, response.interactive)
        return self._send_text(phone, response.text)

    def _send_text(self, phone: str, text: str) -> Optional[str]:
        """Shortcut for sending plain text."""
        try:
            res = self.client.send_message(to=phone, message=text)
            return self.client._extract_message_id(res)
        except Exception as exc:
            logger.error("Failed to send text to %s: %s", phone, exc)
            return None

    def _send_interactive(self, phone: str, data: dict) -> Optional[str]:
        """Shortcut for sending interactive messages."""
        try:
            res = self.client.send_interactive(to=phone, interactive_data=data)
            return self.client._extract_message_id(res)
        except Exception as exc:
            logger.error("Failed to send interactive to %s: %s", phone, exc)
            return None

    def _update_agent_message_id(self, conversation, wamid: str) -> None:
        """Updates the last AGENT message with the WhatsApp Message ID."""
        ConversationMessage.objects.filter(
            conversation=conversation,
            sender="AGENT",
            whatsapp_message_id__isnull=True,
        ).order_by("-created").update(
            whatsapp_message_id=wamid,
            delivery_status=MessageDeliveryStatus.SENT,
        )

    def _download_media(self, media_id: str) -> Optional[bytes]:
        """Download media from Meta Graph API."""
        try:
            token = config("WHATSAPP_CLOUD_ACCESS_TOKEN", default="")
            version = config(
                "WHATSAPP_CLOUD_VISION_API_VERSION", default="v25.0"
            )

            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(
                f"https://graph.facebook.com/{version}/{media_id}",
                headers=headers,
                timeout=15,
            )
            res.raise_for_status()
            url = res.json().get("url")

            if url:
                file_res = requests.get(url, headers=headers, timeout=30)
                file_res.raise_for_status()
                return file_res.content
        except Exception as exc:
            logger.error("Error downloading media %s: %s", media_id, exc)
        return None
