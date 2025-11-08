"""
Base provider interface.

This module defines the abstract base class for all notification providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for notification providers.

    Providers are concrete implementations of messaging services
    (e.g., WhatsApp via Meta API, WHAPI, Twilio, etc.)
    """

    def __init__(self):
        """Initialize the provider."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured.

        Returns:
            bool: True if provider has all required credentials/settings
        """
        pass

    @abstractmethod
    def send_text_message(
        self, recipient: str, message: str, **kwargs
    ) -> Dict[str, any]:
        """
        Send a plain text message.

        Args:
            recipient: Recipient identifier (phone, email, chat_id, etc.)
            message: Text message to send
            **kwargs: Additional provider-specific parameters

        Returns:
            dict: Response with success status and details
                {
                    "success": bool,
                    "message_id": str (optional),
                    "error": str (optional),
                    "response": dict (optional, raw provider response)
                }
        """
        pass

    @abstractmethod
    def send_message_with_button(
        self,
        recipient: str,
        message: str,
        button_text: str,
        button_url: str,
        **kwargs,
    ) -> Dict[str, any]:
        """
        Send a message with an action button.

        Args:
            recipient: Recipient identifier
            message: Text message to send
            button_text: Text to display on the button
            button_url: URL to open when button is clicked
            **kwargs: Additional provider-specific parameters

        Returns:
            dict: Response with success status and details
        """
        pass

    def send_template_message(
        self,
        recipient: str,
        template_name: str,
        template_params: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, any]:
        """
        Send a pre-approved template message.

        This is optional and may not be supported by all providers.

        Args:
            recipient: Recipient identifier
            template_name: Name of the approved template
            template_params: Parameters to fill in the template
            **kwargs: Additional provider-specific parameters

        Returns:
            dict: Response with success status and details
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support template messages"
        )

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient identifier format.

        Args:
            recipient: Recipient identifier to validate

        Returns:
            bool: True if recipient is valid
        """
        return bool(recipient and recipient.strip())

    def handle_error(self, recipient: str, error: Exception) -> Dict[str, any]:
        """
        Handle errors during message sending.

        Args:
            recipient: Recipient identifier
            error: Exception that occurred

        Returns:
            dict: Error response
        """
        error_msg = str(error)
        self.logger.error(
            f"Failed to send message to {recipient} via {self.__class__.__name__}: {error_msg}"
        )
        return {"success": False, "error": error_msg}

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            str: Provider name
        """
        return self.__class__.__name__.replace("Provider", "")

    def get_provider_info(self) -> Dict[str, any]:
        """
        Get information about the provider.

        Returns:
            dict: Provider information
        """
        return {
            "name": self.get_provider_name(),
            "configured": self.is_configured(),
            "supports_buttons": True,  # Override in subclass if needed
            "supports_templates": False,  # Override in subclass if needed
        }
