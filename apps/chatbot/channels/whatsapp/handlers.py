import asyncio
import logging
from typing import Dict, Optional

from constance import config
from django.conf import settings

from apps.chatbot import constants
from apps.chatbot.conversation import ConversationService
from apps.chatbot.services.gemini import GeminiService
from apps.core.services.chats.whatsapp_official import WhatsAppOfficialService

logger = logging.getLogger(__name__)


class WhatsAppBotHandler:
    """Handler for WhatsApp messages via Meta's official Business Cloud API."""

    def __init__(self):
        self.conversation_service = ConversationService()
        self.whatsapp_service = WhatsAppOfficialService()
        self.gemini_service = GeminiService()

    async def handle_webhook(self, webhook_data: Dict) -> Dict:
        """
        Handle incoming webhook from Meta WhatsApp Business Cloud API.

        Meta payload structure:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "WABA_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{ "from": "51999...", "type": "text", "text": {"body": "..."} }],
                        "statuses": [{ "id": "wamid.xxx", "status": "delivered" }]
                    },
                    "field": "messages"
                }]
            }]
        }
        """
        try:
            if webhook_data.get("object") != "whatsapp_business_account":
                logger.warning(f"Unexpected webhook object: {webhook_data.get('object')}")
                return {"status": "ignored"}

            for entry in webhook_data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") != "messages":
                        continue

                    value = change.get("value", {})

                    # Handle incoming messages
                    for message in value.get("messages", []):
                        await self._process_message(message)

                    # Handle status updates (delivered, read, failed)
                    for status in value.get("statuses", []):
                        self._process_status(status)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _process_message(self, message: Dict) -> None:
        """Process a single incoming WhatsApp message."""
        try:
            sender_phone = message.get("from")
            message_type = message.get("type")
            message_id = message.get("id")

            logger.info(f"Processing {message_type} message from {sender_phone} (id={message_id})")

            # Mark as read
            if message_id:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.whatsapp_service.mark_as_read, message_id)

            if message_type == "text":
                await self._handle_text_message(message)
            elif message_type == "image":
                await self._handle_image_message(message)
            elif message_type == "interactive":
                await self._handle_interactive_message(message)
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                await self._send_text_message(
                    sender_phone,
                    "Lo siento, ese tipo de mensaje no es soportado. "
                    "Por favor envía un mensaje de texto.",
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _process_status(self, status: Dict) -> None:
        """Update delivery status on ConversationMessage from Meta webhook."""
        message_id = status.get("id")
        status_value = status.get("status", "").upper()

        logger.info(f"Status update — message {message_id}: {status_value}")

        if not message_id or not status_value:
            return

        from apps.chatbot.models import ConversationMessage
        from apps.chatbot.choices import MessageDeliveryStatus

        status_map = {
            "SENT": MessageDeliveryStatus.SENT,
            "DELIVERED": MessageDeliveryStatus.DELIVERED,
            "READ": MessageDeliveryStatus.READ,
            "FAILED": MessageDeliveryStatus.FAILED,
        }
        delivery_status = status_map.get(status_value)
        if not delivery_status:
            return

        updated = ConversationMessage.objects.filter(
            whatsapp_message_id=message_id
        ).update(delivery_status=delivery_status)

        if updated:
            logger.info(f"Updated delivery status to {delivery_status} for message {message_id}")
        else:
            logger.warning(f"No ConversationMessage found for whatsapp_message_id={message_id}")

    async def _handle_text_message(self, message: Dict) -> None:
        """Handle a text message."""
        sender_phone = message.get("from")
        user_message = message.get("text", {}).get("body", "")

        logger.info(f"Text from {sender_phone}: {user_message}")

        try:
            conversation = await self.conversation_service.aget_or_create_conversation_whatsapp(
                sender_phone
            )

            if not conversation.authenticated:
                (
                    response,
                    image_url,
                ) = await self.conversation_service._ahandle_authentication_whatsapp(
                    conversation, user_message
                )

                await self.conversation_service.asave_message(conversation, "USER", user_message)

                from apps.chatbot.choices import MessageDeliveryStatus
                auth_data = self.conversation_service.intent_detector.extract_auth_data(user_message)
                if image_url and not auth_data:
                    wamid = await self._send_image_message(sender_phone, image_url, response)
                else:
                    wamid = await self._send_text_message(sender_phone, response)

                await self.conversation_service.asave_message(
                    conversation, "AGENT", response,
                    whatsapp_message_id=wamid,
                    delivery_status=MessageDeliveryStatus.SENT if wamid else None,
                )
                return

            response, image_url = await self.conversation_service.aprocess_message_whatsapp(
                sender_phone, user_message
            )

            from apps.chatbot.choices import MessageDeliveryStatus
            if image_url:
                wamid = await self._send_image_message(sender_phone, image_url, response)
            else:
                wamid = await self._send_text_message(sender_phone, response)

            # Update the last AGENT message with the wamid (saved inside aprocess_message_whatsapp)
            if wamid:
                from apps.chatbot.models import ConversationMessage
                ConversationMessage.objects.filter(
                    conversation=conversation,
                    sender="AGENT",
                    whatsapp_message_id__isnull=True,
                ).order_by("-created").first()
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ConversationMessage.objects.filter(
                        conversation=conversation,
                        sender="AGENT",
                        whatsapp_message_id__isnull=True,
                    ).order_by("-created").update(
                        whatsapp_message_id=wamid,
                        delivery_status=MessageDeliveryStatus.SENT,
                    )
                )

        except Exception as e:
            logger.error(f"Error processing text message: {e}", exc_info=True)
            await self._send_text_message(sender_phone, constants.ERROR_PROCESSING_MESSAGE)

    async def _handle_image_message(self, message: Dict) -> None:
        """
        Handle image messages (payment receipts).

        Meta image payload:
        {
            "type": "image",
            "image": {
                "id": "MEDIA_ID",
                "mime_type": "image/jpeg",
                "sha256": "...",
                "caption": "optional caption"
            }
        }
        """
        sender_phone = message.get("from")
        image_data = message.get("image", {})
        caption = image_data.get("caption", "")
        media_id = image_data.get("id")

        logger.info(f"Image from {sender_phone}, media_id={media_id}")

        try:
            conversation = await self.conversation_service.aget_or_create_conversation_whatsapp(
                sender_phone
            )

            if not conversation.authenticated or not conversation.partner:
                await self._send_text_message(
                    sender_phone,
                    "Por favor, autentícate primero enviando tu DNI y año de nacimiento.\n\n"
                    "Ejemplo: DNI 12345678 año 1990",
                )
                return

            # Download image via Meta media endpoint
            image_bytes = await self._download_meta_media(media_id)
            if not image_bytes:
                await self._send_text_message(
                    sender_phone,
                    "❌ No se pudo descargar la imagen. Por favor, intenta nuevamente.",
                )
                return

            extracted_data = self.gemini_service.extract_receipt_data(image_bytes)
            logger.info(f"Extracted receipt data: {extracted_data}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.conversation_service.api_service.upload_payment_receipt,
                conversation.partner.id,
                image_bytes,
                media_id,
                extracted_data.get("amount"),
                extracted_data.get("date"),
                extracted_data.get("notes", ""),
            )

            if result and result.get("id"):
                response_message = (
                    f"✅ *Boleta de pago recibida correctamente*\n\n"
                    f"📝 Número de recibo: {extracted_data.get('document_id')}\n"
                    f"💰 Monto: S/ {result.get('amount')}\n"
                    f"📅 Fecha: {result.get('payment_date')}\n\n"
                    f"Tu boleta está en estado PENDIENTE y será revisada por nuestro equipo.\n\n"
                    f"📝 *Datos procesados del mensaje*\n"
                    f"Si algún dato es incorrecto, nuestro equipo lo corregirá durante la revisión."
                )
                wamid = await self._send_text_message(sender_phone, response_message)
                await self.conversation_service.asave_message(
                    conversation,
                    "USER",
                    f"[IMAGE] {caption}" if caption else "[IMAGE]",
                    metadata={"receipt_id": result.get("document_id"), "media_id": media_id},
                )
                from apps.chatbot.choices import MessageDeliveryStatus
                await self.conversation_service.asave_message(
                    conversation,
                    "AGENT",
                    response_message,
                    whatsapp_message_id=wamid,
                    delivery_status=MessageDeliveryStatus.SENT if wamid else None,
                )
            else:
                await self._send_text_message(
                    sender_phone,
                    "❌ Hubo un error al procesar tu boleta de pago. "
                    "Por favor, intenta nuevamente o contacta con soporte.",
                )

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            await self._send_text_message(sender_phone, constants.ERROR_PROCESSING_MESSAGE)

    async def _handle_interactive_message(self, message: Dict) -> None:
        """Handle interactive messages (button replies, list replies)."""
        sender_phone = message.get("from")
        interactive = message.get("interactive", {})
        interactive_type = interactive.get("type")

        logger.info(f"Interactive ({interactive_type}) from {sender_phone}")

        # Extract the reply text and treat as a regular text message
        reply_text = ""
        if interactive_type == "button_reply":
            reply_text = interactive.get("button_reply", {}).get("title", "")
        elif interactive_type == "list_reply":
            reply_text = interactive.get("list_reply", {}).get("title", "")

        if reply_text:
            # Reuse text handler logic by building a synthetic text message
            synthetic = {"from": sender_phone, "type": "text", "text": {"body": reply_text}}
            await self._handle_text_message(synthetic)
        else:
            await self._send_text_message(
                sender_phone,
                "Mensaje interactivo recibido. Por favor usa comandos de texto.",
            )

    async def _send_text_message(self, recipient_phone: str, message: str) -> Optional[str]:
        """Send a text message via Meta WhatsApp Cloud API. Returns wamid or None."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.whatsapp_service.send_text_message, recipient_phone, message
            )
            if result.get("success"):
                wamid = result.get("message_id")
                logger.info(f"Message sent to {recipient_phone} (id={wamid})")
                return wamid
            else:
                logger.error(f"Failed to send to {recipient_phone}: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error sending text message: {e}", exc_info=True)
            return None

    async def _send_image_message(
        self, recipient_phone: str, image_url: str, caption: str
    ) -> Optional[str]:
        """Send an image message via Meta WhatsApp Cloud API. Returns wamid or None."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.whatsapp_service.send_image_message,
                recipient_phone,
                image_url,
                caption,
            )
            if result.get("success"):
                wamid = result.get("message_id")
                logger.info(f"Image sent to {recipient_phone} (id={wamid})")
                return wamid
            else:
                logger.error(f"Failed to send image to {recipient_phone}: {result.get('error')}")
                await self._send_text_message(recipient_phone, caption)
                return None
        except Exception as e:
            logger.error(f"Error sending image: {e}", exc_info=True)
            await self._send_text_message(recipient_phone, caption)
            return None

    async def _download_meta_media(self, media_id: str) -> Optional[bytes]:
        """
        Download media from Meta using the media ID.

        Meta requires two steps:
        1. GET /v19.0/{media_id} → returns a temporary download URL
        2. GET {url} with Bearer token → returns the file bytes
        """
        try:
            access_token = getattr(settings, "WHATSAPP_API_TOKEN", None)
            api_version = getattr(settings, "WHATSAPP_API_VERSION", "v21.0")
            if not access_token:
                logger.error("WHATSAPP_API_TOKEN not set, cannot download media")
                return None

            headers = {"Authorization": f"Bearer {access_token}"}

            import requests as _requests

            # Step 1: resolve media URL
            meta_response = _requests.get(
                f"https://graph.facebook.com/{api_version}/{media_id}",
                headers=headers,
                timeout=15,
            )
            meta_response.raise_for_status()
            media_url = meta_response.json().get("url")

            if not media_url:
                logger.error(f"No URL returned for media_id {media_id}")
                return None

            # Step 2: download the file
            file_response = _requests.get(media_url, headers=headers, timeout=30)
            file_response.raise_for_status()
            return file_response.content

        except Exception as e:
            logger.error(f"Error downloading Meta media {media_id}: {e}", exc_info=True)
            return None

    # ------------------------------------------------------------------ #
    # Sync helpers (used by management commands or Celery tasks)           #
    # ------------------------------------------------------------------ #

    def handle_start_command(self, sender_phone: str) -> None:
        """Send the welcome message (and image if configured)."""
        welcome_message = config.CHATBOT_WELCOME_MESSAGE
        welcome_image = config.CHATBOT_WELCOME_IMAGE

        if welcome_image:
            domain = config.COMPANY_DOMAIN.rstrip("/")
            media_url = settings.MEDIA_URL.strip("/")
            image_url = f"{domain}/{media_url}/constance/{welcome_image}"
            self.whatsapp_service.send_image_message(sender_phone, image_url, welcome_message)
        else:
            self.whatsapp_service.send_text_message(sender_phone, welcome_message)

    def handle_help_command(self, sender_phone: str) -> None:
        """Send the help message."""
        self.whatsapp_service.send_text_message(sender_phone, constants.HELP_MESSAGE)

    def handle_menu_command(self, sender_phone: str) -> None:
        """Send the menu message."""
        response = self.conversation_service.formatter.format_help_message()
        self.whatsapp_service.send_text_message(sender_phone, response)
