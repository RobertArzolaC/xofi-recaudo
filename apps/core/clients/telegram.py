import hmac
import logging
from typing import Any

from decouple import config

from apps.core.clients.base import BaseAPIClient
from apps.core.clients.exceptions import APIClientError, APIValidationError

logger = logging.getLogger(__name__)


class TelegramClient(BaseAPIClient):
    """
    Telegram Bot API client.

    Supports:
    - Send text messages
    - Send media messages (photos, videos, documents)
    - Webhook management (set, delete, get info)
    - Webhook validation
    - Update processing
    """

    def __init__(
        self,
        bot_token: str | None = None,
        webhook_secret: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        """
        Initialize Telegram client.

        Args:
            bot_token: Telegram bot token from BotFather (defaults to settings)
            webhook_secret: Webhook secret token for validation (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        bot_token = bot_token or config("TELEGRAM_BOT_TOKEN", default="")
        timeout = timeout or config("TELEGRAM_TIMEOUT", default=30, cast=int)
        max_retries = max_retries or config("TELEGRAM_MAX_RETRIES", default=3, cast=int)

        # Telegram Bot API URL includes the token
        base_url = f"https://api.telegram.org/bot{bot_token}"

        super().__init__(
            base_url=base_url,
            api_key=None,  # Telegram uses token in URL, not separate API key
            timeout=timeout,
            max_retries=max_retries,
        )

        self.bot_token = bot_token
        self.webhook_secret = webhook_secret or config(
            "TELEGRAM_WEBHOOK_SECRET", default=""
        )

    def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str | None = "HTML",
    ) -> dict[str, Any]:
        """
        Send text message via Telegram.

        Args:
            chat_id: Unique identifier for the target chat or username (@channelusername)
            text: Text of the message to be sent, 1-4096 characters
            parse_mode: Mode for parsing entities (HTML, Markdown, MarkdownV2, or None)

        Returns:
            dict: Response data with message info

        Raises:
            APIValidationError: If chat_id or text is invalid
            APIClientError: If API request fails
        """
        if not text:
            raise APIValidationError("Message text is required")

        payload = {
            "chat_id": str(chat_id),
            "text": text,
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode

        logger.info(f"Sending Telegram message to {chat_id}: {len(text)} characters")

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/sendMessage",
                data=payload,
            )

            if not response_data.get("ok"):
                error_description = response_data.get("description", "Unknown error")
                raise APIClientError(f"Telegram API error: {error_description}")

            result = response_data.get("result", {})
            logger.info(
                f"Message sent successfully: {result.get('message_id', 'unknown')}"
            )
            return result

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise APIClientError(f"Failed to send message: {e}") from e

    def send_photo(
        self,
        chat_id: str | int,
        photo: str,
        caption: str | None = None,
        parse_mode: str | None = "HTML",
    ) -> dict[str, Any]:
        """
        Send photo message via Telegram.

        Args:
            chat_id: Unique identifier for the target chat
            photo: Photo to send (file_id, HTTP URL, or file path)
            caption: Photo caption (0-1024 characters)
            parse_mode: Mode for parsing entities in caption

        Returns:
            dict: Response data with message info

        Raises:
            APIValidationError: If inputs are invalid
            APIClientError: If API request fails
        """
        if not photo:
            raise APIValidationError("Photo is required")

        payload = {
            "chat_id": str(chat_id),
            "photo": photo,
        }

        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode

        logger.info(f"Sending Telegram photo to {chat_id}: {photo}")

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/sendPhoto",
                data=payload,
            )

            if not response_data.get("ok"):
                error_description = response_data.get("description", "Unknown error")
                raise APIClientError(f"Telegram API error: {error_description}")

            result = response_data.get("result", {})
            logger.info(
                f"Photo sent successfully: {result.get('message_id', 'unknown')}"
            )
            return result

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending photo: {e}")
            raise APIClientError(f"Failed to send photo: {e}") from e

    def send_document(
        self,
        chat_id: str | int,
        document: str,
        caption: str | None = None,
        parse_mode: str | None = "HTML",
    ) -> dict[str, Any]:
        """
        Send document message via Telegram.

        Args:
            chat_id: Unique identifier for the target chat
            document: Document to send (file_id, HTTP URL, or file path)
            caption: Document caption (0-1024 characters)
            parse_mode: Mode for parsing entities in caption

        Returns:
            dict: Response data with message info

        Raises:
            APIValidationError: If inputs are invalid
            APIClientError: If API request fails
        """
        if not document:
            raise APIValidationError("Document is required")

        payload = {
            "chat_id": str(chat_id),
            "document": document,
        }

        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode

        logger.info(f"Sending Telegram document to {chat_id}: {document}")

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/sendDocument",
                data=payload,
            )

            if not response_data.get("ok"):
                error_description = response_data.get("description", "Unknown error")
                raise APIClientError(f"Telegram API error: {error_description}")

            result = response_data.get("result", {})
            logger.info(
                f"Document sent successfully: {result.get('message_id', 'unknown')}"
            )
            return result

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending document: {e}")
            raise APIClientError(f"Failed to send document: {e}") from e

    def set_webhook(
        self,
        url: str,
        secret_token: str | None = None,
    ) -> bool:
        """
        Set webhook URL for receiving updates.

        Args:
            url: HTTPS URL to send updates to. Use an empty string to remove webhook
            secret_token: Secret token to be sent in header "X-Telegram-Bot-Api-Secret-Token"

        Returns:
            bool: True if successful

        Raises:
            APIValidationError: If URL is invalid
            APIClientError: If API request fails
        """
        if not url:
            raise APIValidationError("Webhook URL is required")

        payload = {"url": url}

        if secret_token or self.webhook_secret:
            payload["secret_token"] = secret_token or self.webhook_secret

        logger.info(f"Setting Telegram webhook: {url}")

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/setWebhook",
                data=payload,
            )

            if response_data.get("ok"):
                logger.info("Webhook set successfully")
                return True

            error_description = response_data.get("description", "Unknown error")
            logger.error(f"Failed to set webhook: {error_description}")
            return False

        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    def delete_webhook(self) -> bool:
        """
        Remove webhook integration.

        Returns:
            bool: True if successful
        """
        logger.info("Deleting Telegram webhook")

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/deleteWebhook",
            )

            if response_data.get("ok"):
                logger.info("Webhook deleted successfully")
                return True

            logger.error("Failed to delete webhook")
            return False

        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    def get_webhook_info(self) -> dict[str, Any]:
        """
        Get current webhook status and information.

        Returns:
            dict: Webhook information including URL, pending update count, etc.
        """
        logger.info("Getting Telegram webhook info")

        try:
            response_data = self._make_request(
                method="GET",
                endpoint="/getWebhookInfo",
            )

            if response_data.get("ok"):
                return response_data.get("result", {})

            logger.error("Failed to get webhook info")
            return {}

        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {}

    # Placeholder values that should be treated as "not configured"
    _PLACEHOLDER_SECRETS = frozenset({
        "your-telegram-webhook-secret",
        "your_webhook_secret_here",
        "changeme",
        "secret",
    })

    def validate_webhook(self, secret_token: str, received_token: str) -> bool:
        """
        Validate webhook request using secret token.

        Telegram sends the secret token in the X-Telegram-Bot-Api-Secret-Token header.
        If the configured secret is empty or a known placeholder, validation is skipped
        and all requests are accepted (useful for development environments).

        Args:
            secret_token: Expected secret token (from TELEGRAM_WEBHOOK_SECRET env var)
            received_token: Token from X-Telegram-Bot-Api-Secret-Token header

        Returns:
            bool: True if valid
        """
        if not secret_token or secret_token in self._PLACEHOLDER_SECRETS:
            logger.warning(
                "Webhook secret not configured or is a placeholder — skipping validation"
            )
            return True  # Allow if not configured

        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(secret_token, received_token)

        if is_valid:
            logger.info("Telegram webhook validation successful")
        else:
            logger.warning("Telegram webhook validation failed")

        return is_valid

    def get_file_url(self, file_id: str) -> str:
        """
        Convert a Telegram file_id to a downloadable URL.

        Calls /getFile to obtain the file_path, then constructs the full URL.

        Args:
            file_id: Telegram file identifier received in webhook updates.

        Returns:
            str: Full HTTPS URL to download the file.

        Raises:
            APIClientError: If the API request fails or file_id is invalid.
        """
        if not file_id:
            raise APIValidationError("file_id is required")

        try:
            response_data = self._make_request(
                method="GET",
                endpoint="/getFile",
                params={"file_id": file_id},
            )

            if not response_data.get("ok"):
                error_description = response_data.get("description", "Unknown error")
                raise APIClientError(f"Telegram API error: {error_description}")

            file_path = response_data.get("result", {}).get("file_path")
            if not file_path:
                raise APIClientError("No file_path in Telegram getFile response")

            return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Error getting file URL for {file_id}: {e}")
            raise APIClientError(f"Failed to get file URL: {e}") from e

    def get_me(self) -> dict[str, Any]:
        """
        Get basic information about the bot.

        Returns:
            dict: Bot information (id, username, first_name, etc.)

        Raises:
            APIClientError: If API request fails
        """
        logger.info("Getting bot information")

        try:
            response_data = self._make_request(
                method="GET",
                endpoint="/getMe",
            )

            if response_data.get("ok"):
                result = response_data.get("result", {})
                logger.info(f"Bot info retrieved: @{result.get('username', 'unknown')}")
                return result

            raise APIClientError("Failed to get bot information")

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting bot info: {e}")
            raise APIClientError(f"Failed to get bot info: {e}") from e

    def validate_api_key(self) -> bool:
        """
        Validate Telegram bot token by calling getMe.

        Returns:
            bool: True if bot token is valid
        """
        if not self.bot_token:
            logger.error("No bot token configured")
            return False

        try:
            self.get_me()
            logger.info("Bot token validation successful")
            return True

        except Exception as e:
            logger.error(f"Bot token validation failed: {e}")
            return False

    def health_check(self) -> bool:
        """
        Check if Telegram API is healthy.

        Returns:
            bool: True if API is accessible
        """
        try:
            self.get_me()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
