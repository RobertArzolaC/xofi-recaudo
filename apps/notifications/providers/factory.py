import logging
from typing import Optional

from django.conf import settings

from apps.campaigns import choices
from apps.notifications.providers.base import BaseProvider
from apps.notifications.providers.telegram import TelegramBotProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating notification providers.

    This factory determines which provider to use based on:
    1. Channel type (WhatsApp, Telegram, Email, SMS)
    2. Configuration settings (which provider is configured)
    3. Explicit provider preference (optional)
    """

    @classmethod
    def get_provider(cls, channel: str) -> Optional[BaseProvider]:
        """
        Get a provider instance for the specified channel.

        Args:
            channel: Notification channel (from choices.NotificationChannel)
            provider_name: Optional specific provider name to use

        Returns:
            BaseProvider: Provider instance or None if not available
        """

        if channel == choices.NotificationChannel.WHATSAPP:
            return cls._get_whatsapp_provider()
        elif channel == choices.NotificationChannel.TELEGRAM:
            return cls._get_telegram_provider()
        elif channel == choices.NotificationChannel.EMAIL:
            return cls._get_email_provider()
        elif channel == choices.NotificationChannel.SMS:
            return cls._get_sms_provider()
        else:
            logger.error(f"Unsupported channel: {channel}")
            return None

    @classmethod
    def _get_whatsapp_provider(cls) -> Optional[BaseProvider]:
        """
        Get WhatsApp provider.

        Returns:
            BaseProvider: WhatsApp provider instance
        """
        # Check settings
        configured_provider = getattr(
            settings, "WHATSAPP_PROVIDER", "whapi"
        ).lower()
        if configured_provider in cls._WHATSAPP_PROVIDERS:
            provider_class = cls._WHATSAPP_PROVIDERS[configured_provider]
            provider = provider_class()
            if provider.is_configured():
                logger.info(
                    f"Using {provider.get_provider_name()} as WhatsApp provider"
                )
                return provider

        # Return default (even if not configured)
        logger.warning("No WhatsApp provider configured, using Meta as default")
        return cls._WHATSAPP_PROVIDERS.get("meta", lambda: None)()

    @classmethod
    def _get_telegram_provider(cls) -> Optional[BaseProvider]:
        """
        Get Telegram provider.

        Returns:
            BaseProvider: Telegram provider instance
        """

        return TelegramBotProvider()

    @classmethod
    def _get_email_provider(cls) -> Optional[BaseProvider]:
        """
        Get Email provider.

        Returns:
            BaseProvider: Email provider instance (not implemented yet)
        """
        logger.warning("Email providers not implemented yet")
        return None

    @classmethod
    def _get_sms_provider(cls) -> Optional[BaseProvider]:
        """
        Get SMS provider.

        Returns:
            BaseProvider: SMS provider instance (not implemented yet)
        """
        logger.warning("SMS providers not implemented yet")
        return None
