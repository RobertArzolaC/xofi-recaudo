import asyncio
import logging
from typing import Dict, Optional

from django.conf import settings
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending Telegram messages via Telegram Bot API."""

    def __init__(self):
        """Initialize Telegram service with credentials from settings."""
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.bot = None

        if self.token:
            try:
                self.bot = Bot(token=self.token)
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
        else:
            logger.warning(
                "Telegram credentials not configured. "
                "Please set TELEGRAM_BOT_TOKEN in your settings"
            )

    def is_configured(self) -> bool:
        """Check if Telegram service is properly configured."""
        return self.bot is not None

    async def _send_message_async(
        self,
        chat_id: str,
        message: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Dict[str, any]:
        """
        Internal async method to send message.

        Args:
            chat_id: Telegram chat ID or username
            message: Text message to send
            reply_markup: Optional inline keyboard markup

        Returns:
            dict: Response containing success status and message info
        """
        try:
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            logger.info(f"Message sent to {chat_id}: {sent_message.message_id}")
            return {
                "success": True,
                "message_id": sent_message.message_id,
                "chat_id": sent_message.chat_id,
            }
        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return {"success": False, "error": str(e)}

    def send_text_message(
        self, recipient_id: str, message: str
    ) -> Dict[str, any]:
        """
        Send a text message to a Telegram recipient.

        Args:
            recipient_id: Telegram chat ID or username (e.g., @username or 123456789)
            message: Text message to send

        Returns:
            dict: Response containing message ID and status
        """
        if not self.is_configured():
            raise ValueError("Telegram service is not configured")

        # Clean recipient ID (remove @ if present for numeric IDs)
        clean_id = self._clean_recipient_id(recipient_id)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_message_async(clean_id, message)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to send message to {clean_id}: {e}")
            return {"success": False, "error": str(e)}

    def send_message_with_button(
        self,
        recipient_id: str,
        message: str,
        button_text: str,
        button_url: str,
    ) -> Dict[str, any]:
        """
        Send a message with a URL button (for payment links).

        Args:
            recipient_id: Telegram chat ID or username
            message: Text message to send
            button_text: Text to display on the button
            button_url: URL to open when button is clicked

        Returns:
            dict: Response from Telegram API
        """
        if not self.is_configured():
            raise ValueError("Telegram service is not configured")

        clean_id = self._clean_recipient_id(recipient_id)

        try:
            # Create inline keyboard with URL button
            keyboard = [[InlineKeyboardButton(button_text, url=button_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_message_async(clean_id, message, reply_markup)
            )
            loop.close()

            logger.info(f"Message with button sent to {clean_id}")
            return result
        except Exception as e:
            logger.error(
                f"Failed to send message with button to {clean_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    def _clean_recipient_id(self, recipient_id: str) -> str:
        """
        Clean and format recipient ID for Telegram API.

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
            # Remove all non-digit characters
            clean = "".join(filter(str.isdigit, clean))
        print("clean", clean)

        return clean

    def get_message_status(self, message_id: str) -> Dict[str, any]:
        """
        Get the status of a sent message.

        Args:
            message_id: Telegram message ID

        Returns:
            dict: Message status information

        Note:
            Telegram doesn't provide a direct API to check message status.
            Message delivery can be tracked through bot updates/webhooks.
        """
        logger.info(f"Checking status for message: {message_id}")
        return {"message_id": message_id, "status": "sent"}

    async def verify_bot_async(self) -> Dict[str, any]:
        """
        Verify bot credentials and get bot information.

        Returns:
            dict: Bot information including username and name
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Telegram service is not configured",
            }

        try:
            bot_info = await self.bot.get_me()
            return {
                "success": True,
                "bot_id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
            }
        except TelegramError as e:
            logger.error(f"Failed to verify bot: {e}")
            return {"success": False, "error": str(e)}

    def verify_bot(self) -> Dict[str, any]:
        """
        Verify bot credentials (synchronous wrapper).

        Returns:
            dict: Bot information
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.verify_bot_async())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to verify bot: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
telegram_service = TelegramService()
