import asyncio
import logging
from typing import Dict, Optional

from django.conf import settings
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from apps.notifications.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class TelegramBotProvider(BaseProvider):
    """Telegram provider using the official Bot API."""

    def __init__(self):
        """Initialize Telegram Bot provider."""
        super().__init__()
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.bot = None

        if Bot is None:
            self.logger.warning(
                "python-telegram-bot library not installed. "
                "Install with: pip install python-telegram-bot"
            )
        elif self.token:
            try:
                self.bot = Bot(token=self.token)
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
        else:
            self.logger.warning(
                "Telegram credentials not configured. "
                "Please set TELEGRAM_BOT_TOKEN in your settings"
            )

    def is_configured(self) -> bool:
        """Check if Telegram bot is properly configured."""
        return self.bot is not None

    def send_text_message(
        self, recipient: str, message: str, **kwargs
    ) -> Dict[str, any]:
        """
        Send a text message via Telegram.

        Args:
            recipient: Telegram chat ID or username
            message: Text message to send
            **kwargs: Additional parameters

        Returns:
            dict: Response with success status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Telegram provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient ID"}

        try:
            clean_id = self._clean_recipient_id(recipient)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_message_async(clean_id, message)
            )
            loop.close()
            return result
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
        Send a message with an inline URL button via Telegram.

        Args:
            recipient: Telegram chat ID or username
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
                "error": "Telegram provider is not configured",
            }

        if not self.validate_recipient(recipient):
            return {"success": False, "error": "Invalid recipient ID"}

        try:
            clean_id = self._clean_recipient_id(recipient)

            # Create inline keyboard with URL button
            keyboard = [[InlineKeyboardButton(button_text, url=button_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_message_async(clean_id, message, reply_markup)
            )
            loop.close()

            self.logger.info(f"Message with button sent to {clean_id}")
            return result
        except Exception as e:
            return self.handle_error(recipient, e)

    async def _send_message_async(
        self,
        chat_id: str,
        message: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Dict[str, any]:
        """
        Internal async method to send message.

        Args:
            chat_id: Telegram chat ID
            message: Text message
            reply_markup: Optional keyboard markup

        Returns:
            dict: Response with success status
        """
        try:
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

            self.logger.info(
                f"Message sent to {chat_id}: {sent_message.message_id}"
            )

            return {
                "success": True,
                "message_id": sent_message.message_id,
                "chat_id": sent_message.chat_id,
            }
        except TelegramError as e:
            self.logger.error(f"Failed to send message to {chat_id}: {e}")
            return {"success": False, "error": str(e)}

    def _clean_recipient_id(self, recipient_id: str) -> str:
        """
        Clean and format recipient ID for Telegram.

        Args:
            recipient_id: Telegram chat ID or username

        Returns:
            str: Clean recipient ID
        """
        if not recipient_id:
            return ""

        # Remove whitespace
        clean = recipient_id.strip()

        # If it starts with @, keep it (username format)
        # Otherwise, ensure it's numeric (chat ID)
        if not clean.startswith("@"):
            clean = "".join(filter(str.isdigit, clean))

        return clean

    def get_provider_info(self) -> Dict[str, any]:
        """Get Telegram Bot provider information."""
        return {
            "name": "Telegram Bot API",
            "configured": self.is_configured(),
            "supports_buttons": True,
            "supports_templates": False,
        }
