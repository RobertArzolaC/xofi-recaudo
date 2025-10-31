"""Telegram bot handlers for AI agent."""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apps.ai_agent import constants
from apps.ai_agent.services.conversation_service import ConversationService
from apps.core.services.chats.telegram import TelegramService

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """Handler for Telegram bot commands and messages."""

    def __init__(self):
        """Initialize handlers and services."""
        self.conversation_service = ConversationService()
        self.telegram_service = TelegramService()

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)

        logger.info(f"Received /start from chat {chat_id}")

        await update.message.reply_text(
            constants.WELCOME_MESSAGE, parse_mode="Markdown"
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
            # Process message through conversation service (async)
            response = await self.conversation_service.aprocess_message(
                chat_id, user_message, username
            )

            # Send response
            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await update.message.reply_text(constants.ERROR_PROCESSING_MESSAGE)

    async def handle_photo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle photo uploads (payment receipts)."""
        chat_id = str(update.effective_chat.id)

        logger.info(f"Received photo from {chat_id}")

        # TODO: Implement payment receipt processing
        # This would involve:
        # 1. Download the photo
        # 2. Process with OCR/AI to extract payment info
        # 3. Create payment receipt record
        # 4. Associate with partner
        # Variables like photo and caption will be used when implementing the above

        await update.message.reply_text(
            constants.PHOTO_RECEIVED_MESSAGE, parse_mode="Markdown"
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
    """
    Setup all handlers for the Telegram bot.

    Args:
        application: Telegram bot application instance
    """
    handler = TelegramBotHandler()

    # Command handlers
    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("menu", handler.menu_command))

    # Message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handler.handle_photo))

    # Error handler
    application.add_error_handler(handler.error_handler)

    logger.info("Telegram bot handlers setup completed")
