import asyncio
import logging
from typing import Dict, Optional

import requests

from apps.chatbot import constants
from apps.chatbot.conversation import ConversationService
from apps.chatbot.services.gemini import GeminiService
from apps.core.services.chats.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)


class WhatsAppBotHandler:
    """Handler for WhatsApp bot messages and media."""

    def __init__(self):
        """Initialize handlers and services."""
        self.conversation_service = ConversationService()
        self.whatsapp_service = WhatsAppService()
        self.gemini_service = GeminiService()

    async def handle_webhook(self, webhook_data: Dict) -> Dict[str, any]:
        """
        Handle incoming WhatsApp webhook from WHAPI.

        WHAPI webhook structure:
        {
            "messages": [...],
            "event": {"type": "messages", "event": "post"},
            "channel_id": "..."
        }

        Args:
            webhook_data: Webhook payload from WHAPI

        Returns:
            dict: Response data
        """
        try:
            # Extract messages from WHAPI structure
            messages = webhook_data.get("messages", [])
            event = webhook_data.get("event", {})
            event_type = event.get("type", "")

            if event_type != constants.WHAPI_EVENT_TYPE_MESSAGES:
                logger.warning(f"Unsupported event type: {event_type}")
                return {"status": "unsupported_event"}

            if not messages:
                logger.warning("No messages in webhook data")
                return {"status": "no_messages"}

            # Process each message
            for message in messages:
                message_from = message.get("from")
                # Whapi sends messages sent by the bot itself; filter them out
                only_number = message_from != "51931314241"
                # Ignore messages sent by bot (from_me = true) or only_number is False
                if message.get("from_me", False) or only_number:
                    logger.info(
                        f"Ignoring message from bot: {message.get('id')}"
                    )
                    continue

                await self._process_message(message)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _process_message(self, message: Dict) -> None:
        """
        Process a single WhatsApp message.

        Args:
            message: Message data from webhook
        """
        try:
            # Extract message info
            sender_phone = message.get("from")
            message_type = message.get("type")

            logger.info(
                f"Processing message from {sender_phone}, type: {message_type}"
            )

            # Handle different message types
            if message_type == "text":
                await self._handle_text_message(message)
            elif message_type == "image":
                await self._handle_image_message(message)
            elif message_type == "interactive":
                await self._handle_interactive_message(message)
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                # Send unsupported message notification
                await self._send_text_message(
                    sender_phone,
                    "Lo siento, ese tipo de mensaje no es soportado. "
                    "Por favor envía un mensaje de texto.",
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def _handle_text_message(self, message: Dict) -> None:
        """
        Handle text messages.

        Args:
            message: Text message data
        """
        sender_phone = message.get("from")
        text_data = message.get("text", {})
        user_message = text_data.get("body", "")

        logger.info(f"Received text from {sender_phone}: {user_message}")

        try:
            # Process message through conversation service (async)
            response = (
                await self.conversation_service.aprocess_message_whatsapp(
                    sender_phone, user_message
                )
            )

            # Send response
            await self._send_text_message(sender_phone, response)

        except Exception as e:
            logger.error(f"Error processing text message: {e}", exc_info=True)
            await self._send_text_message(
                sender_phone, constants.ERROR_PROCESSING_MESSAGE
            )

    async def _handle_image_message(self, message: Dict) -> None:
        """
        Handle image messages (payment receipts).

        Args:
            message: Image message data
        """
        sender_phone = message.get("from")
        image_data = message.get("image", {})
        caption = image_data.get("caption", "")
        image_link = image_data.get("link")
        image_id = image_data.get("id")

        image_bytes = None

        logger.info(f"Received image from {sender_phone}, ID: {image_id}")

        try:
            # Get or create conversation
            conversation = await self.conversation_service.aget_or_create_conversation_whatsapp(
                sender_phone
            )

            # Check if user is authenticated
            if not conversation.authenticated or not conversation.partner:
                await self._send_text_message(
                    sender_phone,
                    "Por favor, autentícate primero enviando tu DNI y año de nacimiento.\n\n"
                    "Ejemplo: DNI 12345678 año 1990",
                )
                return

            # Download the image using the direct link
            if not image_link:
                await self._send_text_message(
                    sender_phone,
                    "❌ No se encontró el enlace de la imagen. Por favor, intenta nuevamente.",
                )
                return

            image_bytes = await self._download_media(image_link)
            if not image_bytes:
                await self._send_text_message(
                    sender_phone,
                    "❌ No se pudo descargar la imagen. Por favor, intenta nuevamente.",
                )
                return

            # Extract receipt data using the dedicated service
            logger.info("Extracting receipt data using extraction service...")
            result = self.gemini_service.extract_receipt_data(image_bytes)

            # Run synchronous API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.conversation_service.api_service.upload_payment_receipt,
                conversation.partner.id,
                image_bytes,
                image_id,
                result.get("amount"),
                result.get("date"),
                result.get("notes"),
            )

            if result and result.get("id"):
                # Success
                response_message = (
                    f"✅ *Boleta de pago recibida correctamente*\n\n"
                    f"📝 Número de recibo: {result.get('id')}\n"
                    f"💰 Monto: S/ {result.get('amount'):.2f}\n"
                    f"📅 Fecha: {result.get('date')}\n\n"
                    f"Tu boleta está en estado PENDIENTE y será revisada por nuestro equipo.\n\n"
                )

                # Add contextual feedback based on data quality
                if result.get("amount"):
                    response_message += (
                        "📝 *Datos procesados del mensaje*\n"
                        "Si algún dato es incorrecto, nuestro equipo lo corregirá durante la revisión."
                    )

                await self._send_text_message(sender_phone, response_message)

                # Save message to conversation
                await self.conversation_service.asave_message(
                    conversation,
                    "USER",
                    f"[IMAGE] {caption}" if caption else "[IMAGE]",
                    metadata={
                        "receipt_id": result.get("id"),
                        "filename": image_id,
                        "image_link": image_link,
                    },
                )
            else:
                await self._send_text_message(
                    sender_phone,
                    "❌ Hubo un error al procesar tu boleta de pago. "
                    "Por favor, intenta nuevamente o contacta con soporte.",
                )

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            await self._send_text_message(
                sender_phone, constants.ERROR_PROCESSING_MESSAGE
            )

    async def _handle_interactive_message(self, message: Dict) -> None:
        """
        Handle interactive messages (button clicks).

        Args:
            message: Interactive message data
        """
        sender_phone = message.get("from")

        logger.info(f"Received interactive message from {sender_phone}")

        # For now, just acknowledge
        await self._send_text_message(
            sender_phone,
            "Mensaje interactivo recibido. Por favor usa comandos de texto.",
        )

    async def _handle_status_update(self, status: Dict) -> Dict[str, str]:
        """
        Handle message status updates.

        Args:
            status: Status update data

        Returns:
            dict: Processing result
        """
        message_id = status.get("id")
        status_value = status.get("status")

        logger.info(f"Message {message_id} status: {status_value}")

        return {"status": "status_update_received"}

    async def _send_text_message(
        self, recipient_phone: str, message: str
    ) -> None:
        """
        Send a text message via WhatsApp.

        Args:
            recipient_phone: Recipient's phone number
            message: Message text to send
        """
        try:
            # Run sync WhatsApp send in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.whatsapp_service.send_text_message,
                recipient_phone,
                message,
            )

            if result.get("success"):
                logger.info(f"Message sent to {recipient_phone}")
            else:
                logger.error(
                    f"Failed to send message to {recipient_phone}: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Error sending text message: {e}", exc_info=True)

    async def _download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media file from the provided URL.

        Args:
            media_url: Direct URL to the media file

        Returns:
            bytes: Media file content, or None if failed
        """
        try:
            # Download media directly from the URL provided by WHAPI
            response = requests.get(media_url)
            response.raise_for_status()

            return response.content

        except Exception as e:
            logger.error(
                f"Error downloading media from URL {media_url}: {e}",
                exc_info=True,
            )
            return None

    def handle_start_command(self, sender_phone: str) -> None:
        """
        Handle /start equivalent command.

        Args:
            sender_phone: Sender's phone number
        """
        logger.info(f"Sending welcome message to {sender_phone}")

        self.whatsapp_service.send_text_message(
            sender_phone, constants.WELCOME_MESSAGE
        )

    def handle_help_command(self, sender_phone: str) -> None:
        """
        Handle /help equivalent command.

        Args:
            sender_phone: Sender's phone number
        """
        logger.info(f"Sending help message to {sender_phone}")

        self.whatsapp_service.send_text_message(
            sender_phone, constants.HELP_MESSAGE
        )

    def handle_menu_command(self, sender_phone: str) -> None:
        """
        Handle /menu equivalent command.

        Args:
            sender_phone: Sender's phone number
        """
        response = self.conversation_service.formatter.format_help_message()
        self.whatsapp_service.send_text_message(sender_phone, response)
