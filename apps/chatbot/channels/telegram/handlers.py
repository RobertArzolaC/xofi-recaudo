import asyncio
import logging

from constance import config
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apps.chatbot import constants
from apps.chatbot.conversation import ConversationService
from apps.chatbot.services.receipt_extraction import (
    ReceiptDataExtractionService,
)
from apps.core.services.chats.telegram import TelegramService

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """Handler for Telegram bot commands and messages."""

    def __init__(self):
        self.conversation_service = ConversationService()
        self.telegram_service = TelegramService()
        self.receipt_extraction_service = ReceiptDataExtractionService()

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        logger.info(f"Received /start from chat {chat_id}")
        await update.message.reply_text(
            config.CHATBOT_WELCOME_MESSAGE, parse_mode="Markdown"
        )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        chat_id = str(update.effective_chat.id)
        logger.info(f"Received /help from chat {chat_id}")
        await update.message.reply_text(
            constants.HELP_MESSAGE, parse_mode="Markdown"
        )

    async def menu_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /menu command."""
        response = self.conversation_service.formatter.format_help_message()
        await update.message.reply_text(response, parse_mode="Markdown")

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle regular text messages."""
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or ""
        user_message = update.message.text

        logger.info(f"Received message from {chat_id}: {user_message}")

        try:
            response = await self.conversation_service.aprocess_message(
                chat_id, user_message, username
            )
            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await update.message.reply_text(constants.ERROR_PROCESSING_MESSAGE)

    async def handle_photo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle photo uploads (payment receipts)."""
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or ""
        caption = update.message.caption or ""

        logger.info(f"Received photo from {chat_id}")

        try:
            conversation = (
                await self.conversation_service.aget_or_create_conversation(
                    chat_id, username
                )
            )

            if not conversation.authenticated or not conversation.partner:
                await update.message.reply_text(
                    "Por favor, autentícate primero enviando tu DNI y año de nacimiento.\n\n"
                    "Ejemplo: DNI 12345678 año 1990",
                    parse_mode="Markdown",
                )
                return

            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            photo_bytes = await photo_file.download_as_bytearray()

            amount, payment_date, filename, notes = (
                self.receipt_extraction_service.prepare_receipt_data(
                    caption=caption,
                    partner_id=conversation.partner.id,
                    chat_id=chat_id,
                    file_unique_id=photo.file_unique_id,
                    file_path=photo_file.file_path,
                )
            )

            from apps.chatbot.services.partner_api import PartnerAPIService

            api_service = PartnerAPIService()

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                api_service.upload_payment_receipt,
                conversation.partner.id,
                bytes(photo_bytes),
                filename,
                amount,
                payment_date,
                notes,
            )

            if result and result.get("id"):
                response_message = (
                    f"✅ *Boleta de pago recibida correctamente*\n\n"
                    f"📝 Número de recibo: {result.get('id')}\n"
                    f"💰 Monto: S/ {amount:.2f}\n"
                    f"📅 Fecha: {payment_date}\n\n"
                    f"Tu boleta está en estado PENDIENTE y será revisada por nuestro equipo.\n\n"
                    f"📝 *Datos procesados del mensaje*\n"
                    f"Si algún dato es incorrecto, nuestro equipo lo corregirá durante la revisión."
                )
                await update.message.reply_text(
                    response_message, parse_mode="Markdown"
                )
                await self.conversation_service.asave_message(
                    conversation,
                    "USER",
                    f"[PHOTO] {caption}" if caption else "[PHOTO]",
                    metadata={
                        "receipt_id": result.get("id"),
                        "filename": filename,
                    },
                )
            else:
                await update.message.reply_text(
                    "❌ Hubo un error al procesar tu boleta de pago. "
                    "Por favor, intenta nuevamente o contacta con soporte.",
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error processing photo: {e}", exc_info=True)
            await update.message.reply_text(
                constants.ERROR_PROCESSING_MESSAGE, parse_mode="Markdown"
            )

    async def error_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors."""
        logger.error(
            f"Update {update} caused error {context.error}", exc_info=True
        )
        if update and update.effective_message:
            await update.effective_message.reply_text(
                constants.UNEXPECTED_ERROR_MESSAGE
            )


def setup_handlers(application: Application) -> None:
    """Setup all handlers for the Telegram bot."""
    handler = TelegramBotHandler()

    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("menu", handler.menu_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handler.handle_photo))
    application.add_error_handler(handler.error_handler)

    logger.info("Telegram bot handlers setup completed")
