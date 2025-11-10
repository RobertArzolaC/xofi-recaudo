import logging
from typing import Dict, Optional

from django.conf import settings

from apps.campaigns import choices
from apps.notifications.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating notification providers.

    This factory determines which provider to use based on:
    1. Channel type (WhatsApp, Telegram, Email, SMS)
    2. Configuration settings (which provider is configured)
    3. Explicit provider preference (optional)
    """

    # Provider registry by channel
    _WHATSAPP_PROVIDERS = {}
    _TELEGRAM_PROVIDERS = {}
    _EMAIL_PROVIDERS = {}
    _SMS_PROVIDERS = {}

    @classmethod
    def register_providers(cls):
        """
        Register all available providers.

        This method is called once to populate the provider registry.
        """
        # Register WhatsApp providers
        try:
            from apps.notifications.providers.whatsapp import (
                MetaWhatsAppProvider,
                WHAPIProvider,
            )

            cls._WHATSAPP_PROVIDERS = {
                "meta": MetaWhatsAppProvider,
                "whapi": WHAPIProvider,
            }
        except ImportError as e:
            logger.warning(f"Failed to import WhatsApp providers: {e}")

        # Register Telegram providers
        try:
            from apps.notifications.providers.telegram import (
                TelegramBotProvider,
            )

            cls._TELEGRAM_PROVIDERS = {
                "telegram_bot": TelegramBotProvider,
            }
        except ImportError as e:
            logger.warning(f"Failed to import Telegram providers: {e}")

        logger.info("Providers registered successfully")

    @classmethod
    def get_provider(
        cls, channel: str, provider_name: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """
        Get a provider instance for the specified channel.

        Args:
            channel: Notification channel (from choices.NotificationChannel)
            provider_name: Optional specific provider name to use

        Returns:
            BaseProvider: Provider instance or None if not available
        """
        if not cls._WHATSAPP_PROVIDERS:
            cls.register_providers()

        if channel == choices.NotificationChannel.WHATSAPP:
            return cls._get_whatsapp_provider(provider_name)
        elif channel == choices.NotificationChannel.TELEGRAM:
            return cls._get_telegram_provider(provider_name)
        elif channel == choices.NotificationChannel.EMAIL:
            return cls._get_email_provider(provider_name)
        elif channel == choices.NotificationChannel.SMS:
            return cls._get_sms_provider(provider_name)
        else:
            logger.error(f"Unsupported channel: {channel}")
            return None

    @classmethod
    def _get_whatsapp_provider(
        cls, provider_name: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """
        Get WhatsApp provider.

        Priority:
        1. Explicit provider_name if specified
        2. WHATSAPP_PROVIDER setting
        3. First configured provider found
        4. Default to Meta provider

        Args:
            provider_name: Optional provider name

        Returns:
            BaseProvider: WhatsApp provider instance
        """
        # Check explicit provider name
        if provider_name and provider_name in cls._WHATSAPP_PROVIDERS:
            provider_class = cls._WHATSAPP_PROVIDERS[provider_name]
            return provider_class()

        # Check settings
        configured_provider = getattr(
            settings, "WHATSAPP_PROVIDER", "meta"
        ).lower()
        if configured_provider in cls._WHATSAPP_PROVIDERS:
            provider_class = cls._WHATSAPP_PROVIDERS[configured_provider]
            provider = provider_class()
            if provider.is_configured():
                return provider

        # Try to find any configured provider
        for provider_class in cls._WHATSAPP_PROVIDERS.values():
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
    def _get_telegram_provider(
        cls, provider_name: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """
        Get Telegram provider.

        Args:
            provider_name: Optional provider name

        Returns:
            BaseProvider: Telegram provider instance
        """
        # For now, only one Telegram provider
        if "telegram_bot" in cls._TELEGRAM_PROVIDERS:
            return cls._TELEGRAM_PROVIDERS["telegram_bot"]()

        logger.error("No Telegram provider available")
        return None

    @classmethod
    def _get_email_provider(
        cls, provider_name: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """
        Get Email provider.

        Args:
            provider_name: Optional provider name

        Returns:
            BaseProvider: Email provider instance (not implemented yet)
        """
        logger.warning("Email providers not implemented yet")
        return None

    @classmethod
    def _get_sms_provider(
        cls, provider_name: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """
        Get SMS provider.

        Args:
            provider_name: Optional provider name

        Returns:
            BaseProvider: SMS provider instance (not implemented yet)
        """
        logger.warning("SMS providers not implemented yet")
        return None

    @classmethod
    def get_available_providers(cls, channel: str) -> Dict[str, Dict]:
        """
        Get information about available providers for a channel.

        Args:
            channel: Notification channel

        Returns:
            dict: Dictionary of provider names and their info
        """
        if not cls._WHATSAPP_PROVIDERS:
            cls.register_providers()

        providers_info = {}

        if channel == choices.NotificationChannel.WHATSAPP:
            for name, provider_class in cls._WHATSAPP_PROVIDERS.items():
                provider = provider_class()
                providers_info[name] = provider.get_provider_info()
        elif channel == choices.NotificationChannel.TELEGRAM:
            for name, provider_class in cls._TELEGRAM_PROVIDERS.items():
                provider = provider_class()
                providers_info[name] = provider.get_provider_info()

        return providers_info
