import logging
from typing import Dict, Optional

import requests
from celery import shared_task
from django.conf import settings

from apps.chatbot import constants
from apps.chatbot.choices import MessageDeliveryStatus
from apps.chatbot.conversation import ConversationService
from apps.chatbot.models import ConversationMessage
from apps.chatbot.services.authentication import PartnerAuthenticationService
from apps.chatbot.services.gemini import GeminiService
from apps.chatbot.services.partner_api import PartnerAPIService
from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient

logger = logging.getLogger(__name__)


@shared_task(
    name="chatbot.process_whatsapp_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_whatsapp_webhook(self, webhook_data: Dict) -> Dict:
    """
    Process an incoming Meta WhatsApp Business Cloud API webhook payload.

    Dispatched asynchronously from WhatsAppWebhookView so Meta receives
    an immediate 200 response while all processing happens in the background.
    """
    try:
        if webhook_data.get("object") != "whatsapp_business_account":
            logger.warning(
                "Unexpected webhook object: %s", webhook_data.get("object")
            )
            return {"status": "ignored"}

        client = WhatsAppCloudAPIClient()
        conv_service = ConversationService()
        gemini_service = GeminiService()
        api_service = PartnerAPIService()

        for entry in webhook_data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue

                value = change.get("value", {})

                for message in value.get("messages", []):
                    _process_message(client, conv_service, gemini_service, api_service, message)

                for status in value.get("statuses", []):
                    _process_status(status)

        return {"status": "success"}

    except Exception as exc:
        logger.error("Error processing webhook: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _process_message(
    client: WhatsAppCloudAPIClient,
    conv_service: ConversationService,
    gemini_service: GeminiService,
    api_service: PartnerAPIService,
    message: Dict,
) -> None:
    """Process a single incoming WhatsApp message."""
    try:
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
                client.mark_message_as_read(message_id)
            except Exception as exc:
                logger.warning("Could not mark message %s as read: %s", message_id, exc)

        if message_type == "text":
            _handle_text_message(client, conv_service, message)
        elif message_type == "image":
            _handle_image_message(client, conv_service, gemini_service, api_service, message)
        elif message_type == "interactive":
            _handle_interactive_message(client, conv_service, message)
        else:
            logger.warning("Unsupported message type: %s", message_type)
            _send_text_message(
                client,
                sender_phone,
                "Lo siento, ese tipo de mensaje no es soportado. "
                "Por favor envía un mensaje de texto.",
            )

    except Exception as exc:
        logger.error("Error processing message: %s", exc, exc_info=True)


def _handle_text_message(
    client: WhatsAppCloudAPIClient,
    conv_service: ConversationService,
    message: Dict,
) -> None:
    """Handle an incoming text message."""
    sender_phone = message.get("from")
    user_message = message.get("text", {}).get("body", "")

    logger.info("Text from %s: %s", sender_phone, user_message)

    try:
        conversation = conv_service.get_or_create_conversation_whatsapp(sender_phone)

        if not conversation.authenticated:
            auth_data = PartnerAuthenticationService.extract_auth_data(user_message)
            conv_service.save_message(conversation, "USER", user_message)
            response = conv_service._handle_authentication(conversation, user_message)

            if auth_data:
                wamid = _send_text_message(client, sender_phone, response)
            else:
                wamid = _send_text_message(client, sender_phone, response)

            conv_service.save_message(
                conversation,
                "AGENT",
                response,
                whatsapp_message_id=wamid,
                delivery_status=MessageDeliveryStatus.SENT if wamid else None,
            )
            return

        response, _ = conv_service.process_message_whatsapp(
            sender_phone, user_message
        )

        wamid = _send_text_message(client, sender_phone, response)

        if wamid:
            ConversationMessage.objects.filter(
                conversation=conversation,
                sender="AGENT",
                whatsapp_message_id__isnull=True,
            ).order_by("-created").update(
                whatsapp_message_id=wamid,
                delivery_status=MessageDeliveryStatus.SENT,
            )

    except Exception as exc:
        logger.error("Error handling text message: %s", exc, exc_info=True)
        _send_text_message(client, sender_phone, constants.ERROR_PROCESSING_MESSAGE)


def _handle_image_message(
    client: WhatsAppCloudAPIClient,
    conv_service: ConversationService,
    gemini_service: GeminiService,
    api_service: PartnerAPIService,
    message: Dict,
) -> None:
    """Handle an incoming image message (payment receipts)."""
    sender_phone = message.get("from")
    image_data = message.get("image", {})
    caption = image_data.get("caption", "")
    media_id = image_data.get("id")

    logger.info("Image from %s, media_id=%s", sender_phone, media_id)

    try:
        conversation = conv_service.get_or_create_conversation_whatsapp(sender_phone)

        if not conversation.authenticated or not conversation.partner:
            _send_text_message(
                client,
                sender_phone,
                "Por favor, autentícate primero enviando tu DNI y año de nacimiento.\n\n"
                "Ejemplo: DNI 12345678 año 1990",
            )
            return

        image_bytes = _download_meta_media(media_id)
        if not image_bytes:
            _send_text_message(
                client,
                sender_phone,
                "❌ No se pudo descargar la imagen. Por favor, intenta nuevamente.",
            )
            return

        extracted_data = gemini_service.extract_receipt_data(image_bytes)
        logger.info("Extracted receipt data: %s", extracted_data)

        result = api_service.upload_payment_receipt(
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
            wamid = _send_text_message(client, sender_phone, response_message)
            conv_service.save_message(
                conversation,
                "USER",
                f"[IMAGE] {caption}" if caption else "[IMAGE]",
                metadata={"receipt_id": result.get("document_id"), "media_id": media_id},
            )
            conv_service.save_message(
                conversation,
                "AGENT",
                response_message,
                whatsapp_message_id=wamid,
                delivery_status=MessageDeliveryStatus.SENT if wamid else None,
            )
        else:
            _send_text_message(
                client,
                sender_phone,
                "❌ Hubo un error al procesar tu boleta de pago. "
                "Por favor, intenta nuevamente o contacta con soporte.",
            )

    except Exception as exc:
        logger.error("Error handling image message: %s", exc, exc_info=True)
        _send_text_message(client, sender_phone, constants.ERROR_PROCESSING_MESSAGE)


def _handle_interactive_message(
    client: WhatsAppCloudAPIClient,
    conv_service: ConversationService,
    message: Dict,
) -> None:
    """Handle interactive messages (button replies, list replies)."""
    sender_phone = message.get("from")
    interactive = message.get("interactive", {})
    interactive_type = interactive.get("type")

    logger.info("Interactive (%s) from %s", interactive_type, sender_phone)

    reply_text = ""
    if interactive_type == "button_reply":
        reply_text = interactive.get("button_reply", {}).get("title", "")
    elif interactive_type == "list_reply":
        reply_text = interactive.get("list_reply", {}).get("title", "")

    if reply_text:
        synthetic = {"from": sender_phone, "type": "text", "text": {"body": reply_text}}
        _handle_text_message(client, conv_service, synthetic)
    else:
        _send_text_message(
            client,
            sender_phone,
            "Mensaje interactivo recibido. Por favor usa comandos de texto.",
        )


def _process_status(status: Dict) -> None:
    """Update delivery status on ConversationMessage from Meta webhook."""
    message_id = status.get("id")
    status_value = status.get("status", "").upper()
    errors = status.get("errors", [])

    if status_value == "FAILED":
        logger.error(
            "WhatsApp delivery FAILED for message %s: %s",
            message_id,
            errors if errors else "No error details",
        )
    else:
        logger.info("Status update — message %s: %s", message_id, status_value)

    if not message_id or not status_value:
        return

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
        logger.info(
            "Updated delivery status to %s for message %s", delivery_status, message_id
        )
    else:
        logger.warning(
            "No ConversationMessage found for whatsapp_message_id=%s", message_id
        )


def _send_text_message(
    client: WhatsAppCloudAPIClient, recipient_phone: str, message: str
) -> Optional[str]:
    """Send a text message via WhatsApp Cloud API. Returns wamid or None."""
    try:
        response = client.send_message(to=recipient_phone, message=message)
        messages = response.get("messages", [])
        wamid = messages[0].get("id") if messages else None
        if wamid:
            logger.info("Text sent to %s (id=%s)", recipient_phone, wamid)
        return wamid
    except Exception as exc:
        logger.error("Error sending text to %s: %s", recipient_phone, exc)
        return None


def _send_image_message(
    client: WhatsAppCloudAPIClient,
    recipient_phone: str,
    image_url: str,
    caption: str,
) -> Optional[str]:
    """Send an image message via WhatsApp Cloud API. Returns wamid or None."""
    try:
        response = client.send_media(
            to=recipient_phone,
            media_url=image_url,
            caption=caption,
            media_type="image",
        )
        messages = response.get("messages", [])
        wamid = messages[0].get("id") if messages else None
        if wamid:
            logger.info("Image sent to %s (id=%s)", recipient_phone, wamid)
        return wamid
    except Exception as exc:
        logger.error("Error sending image to %s: %s — falling back to text", recipient_phone, exc)
        return _send_text_message(client, recipient_phone, caption)


def _download_meta_media(media_id: str) -> Optional[bytes]:
    """
    Download media from Meta using the media ID.

    Meta requires two steps:
    1. GET /{api_version}/{media_id} → returns a temporary download URL
    2. GET {url} with Bearer token → returns the file bytes
    """
    try:
        access_token = getattr(settings, "WHATSAPP_API_TOKEN", None)
        api_version = getattr(settings, "WHATSAPP_API_VERSION", "v21.0")
        if not access_token:
            logger.error("WHATSAPP_API_TOKEN not set, cannot download media")
            return None

        headers = {"Authorization": f"Bearer {access_token}"}

        meta_response = requests.get(
            f"https://graph.facebook.com/{api_version}/{media_id}",
            headers=headers,
            timeout=15,
        )
        meta_response.raise_for_status()
        media_url = meta_response.json().get("url")

        if not media_url:
            logger.error("No URL returned for media_id %s", media_id)
            return None

        file_response = requests.get(media_url, headers=headers, timeout=30)
        file_response.raise_for_status()
        return file_response.content

    except Exception as exc:
        logger.error("Error downloading Meta media %s: %s", media_id, exc, exc_info=True)
        return None
