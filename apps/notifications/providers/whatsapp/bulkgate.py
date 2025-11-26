"""
BulkGate provider for WhatsApp messaging.

This module provides WhatsApp integration using BulkGate API v2.0 Advanced.
Works as an alternative to Meta and WHAPI providers.
"""

import logging
from typing import Dict, Optional

import requests
from django.conf import settings

from apps.notifications.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class BulkGateWhatsAppProvider(BaseProvider):
    """
    BulkGate provider for WhatsApp messaging.

    This is a specialized wrapper around BulkGate's multi-channel API
    specifically for WhatsApp messaging. Use this as an alternative to
    Meta or WHAPI providers.

    API Documentation: https://help.bulkgate.com/docs/en/http-advanced-transactional-v2.html
    """

    # API Configuration
    API_BASE_URL = "https://portal.bulkgate.com/api/2.0"
    TRANSACTIONAL_ENDPOINT = f"{API_BASE_URL}/advanced/transactional"

    # Default settings
    DEFAULT_WHATSAPP_EXPIRATION = 120  # 2 minutes before fallback to SMS

    def __init__(self):
        """Initialize BulkGate WhatsApp provider with credentials from settings."""
        super().__init__()

        self.application_id = getattr(settings, "BULKGATE_APPLICATION_ID", None)
        self.application_token = getattr(
            settings, "BULKGATE_APPLICATION_TOKEN", None
        )
        self.default_sender = getattr(settings, "BULKGATE_DEFAULT_SENDER", None)
        self.default_country = getattr(settings, "BULKGATE_DEFAULT_COUNTRY", "PE")
        self.enable_sms_fallback = getattr(
            settings, "BULKGATE_WHATSAPP_SMS_FALLBACK", True
        )

        if not self.application_id or not self.application_token:
            logger.warning(
                "BulkGate credentials not configured. "
                "Please set BULKGATE_APPLICATION_ID and BULKGATE_APPLICATION_TOKEN"
            )

    def is_configured(self) -> bool:
        """
        Check if BulkGate WhatsApp provider is properly configured.

        Returns:
            bool: True if credentials are set
        """
        return bool(self.application_id and self.application_token)

    def send_text_message(
        self, recipient: str, message: str, **kwargs
    ) -> Dict[str, any]:
        """
        Send a plain text WhatsApp message via BulkGate.

        Args:
            recipient: Phone number in international format (e.g., 51987654321)
            message: Text message to send
            **kwargs: Additional parameters:
                - sender: Custom sender ID
                - country: ISO 3166-1 alpha-2 country code
                - schedule: Unix timestamp or ISO 8601 for delayed sending
                - tag: Message label for tracking
                - enable_sms_fallback: Fall back to SMS if WhatsApp fails

        Returns:
            dict: Response with success status and message details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "BulkGate WhatsApp provider is not configured",
            }

        try:
            clean_number = self._clean_phone_number(recipient)

            # Build request payload with WhatsApp channel
            payload = self._build_whatsapp_payload(
                number=clean_number,
                text=message,
                sender=kwargs.get("sender", self.default_sender),
                country=kwargs.get("country", self.default_country),
                schedule=kwargs.get("schedule"),
                tag=kwargs.get("tag"),
                enable_sms_fallback=kwargs.get(
                    "enable_sms_fallback", self.enable_sms_fallback
                ),
            )

            # Send request
            response = self._make_request(self.TRANSACTIONAL_ENDPOINT, payload)

            if response.get("success"):
                logger.info(
                    f"WhatsApp message sent to {clean_number} via BulkGate. "
                    f"Message ID: {response.get('message_id')}"
                )

            return response

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
        Send a WhatsApp message with a URL button.

        Note: For WhatsApp via BulkGate, buttons are included in the message text.
        For rich button support, use approved WhatsApp templates.

        Args:
            recipient: Phone number in international format
            message: Text message to send
            button_text: Text to display for the button
            button_url: URL to include
            **kwargs: Additional parameters (same as send_text_message)

        Returns:
            dict: Response with success status and details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "BulkGate WhatsApp provider is not configured",
            }

        # Format message with URL
        formatted_message = f"{message}\n\n{button_text}: {button_url}"

        # Use send_text_message with the formatted message
        return self.send_text_message(
            recipient=recipient, message=formatted_message, **kwargs
        )

    def _build_whatsapp_payload(
        self,
        number: str,
        text: str,
        sender: Optional[str] = None,
        country: Optional[str] = None,
        schedule: Optional[str] = None,
        tag: Optional[str] = None,
        enable_sms_fallback: bool = True,
    ) -> Dict[str, any]:
        """
        Build request payload for BulkGate API with WhatsApp channel.

        Args:
            number: Clean phone number
            text: Message text
            sender: Sender ID
            country: Country code
            schedule: Schedule timestamp
            tag: Message tag
            enable_sms_fallback: Enable SMS fallback

        Returns:
            dict: Request payload
        """
        payload = {
            "application_id": self.application_id,
            "application_token": self.application_token,
            "number": number,
            "text": text,
        }

        # Add optional parameters
        if country:
            payload["country"] = country

        if schedule:
            payload["schedule"] = schedule

        if tag:
            payload["tag"] = tag

        # Configure WhatsApp channel with optional SMS fallback
        channel_config = {
            "whatsapp": {
                "sender": sender or "BulkGate",
                "expiration": self.DEFAULT_WHATSAPP_EXPIRATION,
            }
        }

        # Add SMS fallback if enabled
        if enable_sms_fallback:
            channel_config["sms"] = {
                "sender_id": sender or "text",
            }

        payload["channel"] = channel_config

        return payload

    def _make_request(
        self, endpoint: str, payload: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Make HTTP request to BulkGate API.

        Args:
            endpoint: API endpoint URL
            payload: Request payload

        Returns:
            dict: Normalized response
        """
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            # Parse BulkGate response
            return self._parse_response(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"BulkGate WhatsApp API request failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _parse_response(self, response: Dict[str, any]) -> Dict[str, any]:
        """
        Parse and normalize BulkGate API response.

        Args:
            response: Raw API response

        Returns:
            dict: Normalized response
        """
        # Check for error response
        if "error" in response:
            return {
                "success": False,
                "error": response.get("error", {}).get(
                    "description", "Unknown error"
                ),
                "error_type": response.get("error", {}).get("type"),
                "raw_response": response,
            }

        # Success response
        data = response.get("data", {})
        total = data.get("total", {})

        # Extract message IDs and channels
        message_ids = []
        channels_used = []
        responses = data.get("response", [])
        if responses:
            for msg in responses:
                if msg.get("message_id"):
                    message_ids.append(msg.get("message_id"))
                if msg.get("channel"):
                    channels_used.append(msg.get("channel"))

        return {
            "success": total.get("sent", 0) > 0 or total.get("accepted", 0) > 0,
            "message_id": message_ids[0] if message_ids else None,
            "message_ids": message_ids,
            "channels_used": list(set(channels_used)),  # Unique channels
            "total_sent": total.get("sent", 0),
            "total_accepted": total.get("accepted", 0),
            "total_scheduled": total.get("scheduled", 0),
            "total_error": total.get("error", 0),
            "total_blacklisted": total.get("blacklisted", 0),
            "total_invalid": total.get("invalid", 0),
            "responses": responses,
            "raw_response": response,
        }

    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and format phone number for BulkGate.

        BulkGate expects international format without leading zeros or '+'.
        Example: 51987654321 (Peru)

        Args:
            phone: Phone number in any format

        Returns:
            str: Cleaned phone number
        """
        if not phone:
            return ""

        # Remove all non-digit characters
        clean = "".join(filter(str.isdigit, phone))

        # Add default country code if needed (Peru = 51)
        if len(clean) == 9:  # Peruvian number without country code
            clean = f"51{clean}"

        return clean

    def get_provider_info(self) -> Dict[str, any]:
        """
        Get information about the BulkGate WhatsApp provider.

        Returns:
            dict: Provider information
        """
        return {
            "name": "BulkGate WhatsApp",
            "configured": self.is_configured(),
            "supports_buttons": False,  # Only in message text
            "supports_templates": False,  # Not yet implemented
            "supports_bulk": False,  # Use SMS provider for bulk
            "supports_personalization": False,
            "features": {
                "sms_fallback": self.enable_sms_fallback,
                "scheduled_messages": True,
                "message_tracking": True,
            },
            "api_version": "2.0 Advanced",
            "channel": "whatsapp",
        }
