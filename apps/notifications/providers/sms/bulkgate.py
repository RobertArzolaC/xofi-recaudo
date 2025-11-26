"""
BulkGate provider for SMS, Viber, WhatsApp, and RCS messaging.

This module provides integration with BulkGate API v2.0 Advanced.
Supports multiple messaging channels with cascade fallback.
"""

import logging
from typing import Dict, Optional, List

import requests
from django.conf import settings

from apps.notifications.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class BulkGateProvider(BaseProvider):
    """
    BulkGate provider for multi-channel messaging.

    Supports:
    - SMS (primary channel)
    - Viber (business messaging)
    - WhatsApp (messaging)
    - RCS (Rich Communication Services)

    API Documentation: https://help.bulkgate.com/docs/en/http-advanced-transactional-v2.html
    """

    # API Configuration
    API_BASE_URL = "https://portal.bulkgate.com/api/2.0"
    TRANSACTIONAL_ENDPOINT = f"{API_BASE_URL}/advanced/transactional"
    PROMOTIONAL_ENDPOINT = f"{API_BASE_URL}/advanced/promotional"

    # Default settings
    DEFAULT_SMS_EXPIRATION = 300  # 5 minutes
    DEFAULT_VIBER_EXPIRATION = 120  # 2 minutes
    DEFAULT_RCS_EXPIRATION = 120  # 2 minutes

    def __init__(self):
        """Initialize BulkGate provider with credentials from settings."""
        super().__init__()

        self.application_id = getattr(settings, "BULKGATE_APPLICATION_ID", None)
        self.application_token = getattr(settings, "BULKGATE_APPLICATION_TOKEN", None)
        self.default_sender = getattr(settings, "BULKGATE_DEFAULT_SENDER", None)
        self.default_country = getattr(settings, "BULKGATE_DEFAULT_COUNTRY", "PE")

        # Channel preferences
        self.enable_viber = getattr(settings, "BULKGATE_ENABLE_VIBER", False)
        self.enable_whatsapp = getattr(settings, "BULKGATE_ENABLE_WHATSAPP", False)
        self.enable_rcs = getattr(settings, "BULKGATE_ENABLE_RCS", False)

        if not self.application_id or not self.application_token:
            logger.warning(
                "BulkGate credentials not configured. "
                "Please set BULKGATE_APPLICATION_ID and BULKGATE_APPLICATION_TOKEN"
            )

    def is_configured(self) -> bool:
        """
        Check if BulkGate provider is properly configured.

        Returns:
            bool: True if credentials are set
        """
        return bool(self.application_id and self.application_token)

    def send_text_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> Dict[str, any]:
        """
        Send a plain text SMS message.

        Args:
            recipient: Phone number in international format (e.g., 51987654321)
            message: Text message to send (max 612 chars standard, 268 Unicode)
            **kwargs: Additional parameters:
                - sender: Custom sender ID
                - country: ISO 3166-1 alpha-2 country code
                - schedule: Unix timestamp or ISO 8601 for delayed sending
                - tag: Message label for tracking
                - use_cascade: Enable channel cascade (Viber/WhatsApp/RCS fallback)

        Returns:
            dict: Response with success status and message details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "BulkGate provider is not configured"
            }

        try:
            clean_number = self._clean_phone_number(recipient)

            # Build request payload
            payload = self._build_payload(
                number=clean_number,
                text=message,
                sender=kwargs.get("sender", self.default_sender),
                country=kwargs.get("country", self.default_country),
                schedule=kwargs.get("schedule"),
                tag=kwargs.get("tag"),
                use_cascade=kwargs.get("use_cascade", False),
            )

            # Send request
            response = self._make_request(self.TRANSACTIONAL_ENDPOINT, payload)

            if response.get("success"):
                logger.info(
                    f"SMS sent to {clean_number} via BulkGate. "
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
        **kwargs
    ) -> Dict[str, any]:
        """
        Send a message with a URL button.

        Note: Standard SMS doesn't support buttons. The button URL will be
        appended to the message text. For rich buttons, use RCS channel.

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
                "error": "BulkGate provider is not configured"
            }

        # Format message with URL
        formatted_message = f"{message}\n\n{button_text}: {button_url}"

        # Use send_text_message with the formatted message
        return self.send_text_message(
            recipient=recipient,
            message=formatted_message,
            **kwargs
        )

    def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        **kwargs
    ) -> Dict[str, any]:
        """
        Send SMS to multiple recipients.

        Args:
            recipients: List of phone numbers
            message: Text message to send
            **kwargs: Additional parameters (same as send_text_message)

        Returns:
            dict: Response with success status and details for all messages
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "BulkGate provider is not configured"
            }

        if not recipients:
            return {
                "success": False,
                "error": "No recipients provided"
            }

        try:
            # Clean all phone numbers
            clean_numbers = [self._clean_phone_number(num) for num in recipients]

            # Build payload for bulk sending
            payload = self._build_payload(
                number=clean_numbers,
                text=message,
                sender=kwargs.get("sender", self.default_sender),
                country=kwargs.get("country", self.default_country),
                schedule=kwargs.get("schedule"),
                tag=kwargs.get("tag"),
                use_cascade=kwargs.get("use_cascade", False),
            )

            # Send request
            response = self._make_request(self.PROMOTIONAL_ENDPOINT, payload)

            if response.get("success"):
                logger.info(
                    f"Bulk SMS sent to {len(clean_numbers)} recipients via BulkGate"
                )

            return response

        except Exception as e:
            return self.handle_error(str(recipients), e)

    def send_personalized_messages(
        self,
        recipients: List[Dict[str, any]],
        template: str,
        **kwargs
    ) -> Dict[str, any]:
        """
        Send personalized messages using variables.

        Args:
            recipients: List of dicts with 'number' and 'variables' keys
                Example: [
                    {
                        "number": "51987654321",
                        "variables": {"name": "Juan", "amount": "100"}
                    }
                ]
            template: Message template with variables
                Example: "Hola {name}, tu deuda es {amount}"
            **kwargs: Additional parameters

        Returns:
            dict: Response with success status and details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "BulkGate provider is not configured"
            }

        try:
            # Build messages array with variables
            messages = []
            for recipient in recipients:
                messages.append({
                    "number": self._clean_phone_number(recipient.get("number")),
                    "variables": recipient.get("variables", {})
                })

            # Build payload
            payload = {
                "application_id": self.application_id,
                "application_token": self.application_token,
                "number": messages,
                "text": template,
            }

            # Add optional parameters
            if kwargs.get("sender") or self.default_sender:
                payload["sender_id"] = kwargs.get("sender", self.default_sender)

            if kwargs.get("country") or self.default_country:
                payload["country"] = kwargs.get("country", self.default_country)

            # Send request
            response = self._make_request(self.PROMOTIONAL_ENDPOINT, payload)

            if response.get("success"):
                logger.info(
                    f"Personalized messages sent to {len(messages)} recipients"
                )

            return response

        except Exception as e:
            return self.handle_error("bulk_personalized", e)

    def _build_payload(
        self,
        number,
        text: str,
        sender: Optional[str] = None,
        country: Optional[str] = None,
        schedule: Optional[str] = None,
        tag: Optional[str] = None,
        use_cascade: bool = False,
    ) -> Dict[str, any]:
        """
        Build request payload for BulkGate API.

        Args:
            number: Single number or list of numbers
            text: Message text
            sender: Sender ID
            country: Country code
            schedule: Schedule timestamp
            tag: Message tag
            use_cascade: Enable multi-channel cascade

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
        if sender:
            payload["sender_id"] = sender

        if country:
            payload["country"] = country

        if schedule:
            payload["schedule"] = schedule

        if tag:
            payload["tag"] = tag

        # Enable channel cascade if requested
        if use_cascade:
            payload["channel"] = self._build_channel_cascade()

        return payload

    def _build_channel_cascade(self) -> Dict[str, any]:
        """
        Build channel cascade configuration.

        Returns:
            dict: Channel cascade configuration
        """
        channels = {}

        # Add Viber if enabled
        if self.enable_viber:
            channels["viber"] = {
                "sender": self.default_sender or "BulkGate",
                "expiration": self.DEFAULT_VIBER_EXPIRATION,
            }

        # Add WhatsApp if enabled
        if self.enable_whatsapp:
            channels["whatsapp"] = {
                "sender": self.default_sender or "BulkGate",
                "expiration": self.DEFAULT_VIBER_EXPIRATION,
            }

        # Add RCS if enabled
        if self.enable_rcs:
            channels["rcs"] = {
                "sender": self.default_sender or "BulkGate",
                "expiration": self.DEFAULT_RCS_EXPIRATION,
            }

        # SMS is always included as fallback
        channels["sms"] = {
            "sender_id": self.default_sender or "text",
        }

        return channels

    def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, any]
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
            logger.error(f"BulkGate API request failed: {e}")
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
                "error": response.get("error", {}).get("description", "Unknown error"),
                "error_type": response.get("error", {}).get("type"),
                "raw_response": response,
            }

        # Success response
        data = response.get("data", {})
        total = data.get("total", {})

        # Extract message IDs
        message_ids = []
        responses = data.get("response", [])
        if responses:
            message_ids = [
                msg.get("message_id")
                for msg in responses
                if msg.get("message_id")
            ]

        return {
            "success": total.get("sent", 0) > 0 or total.get("accepted", 0) > 0,
            "message_id": message_ids[0] if message_ids else None,
            "message_ids": message_ids,
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
        Get information about the BulkGate provider.

        Returns:
            dict: Provider information
        """
        return {
            "name": "BulkGate",
            "configured": self.is_configured(),
            "supports_buttons": False,  # Only in message text
            "supports_templates": True,
            "supports_bulk": True,
            "supports_personalization": True,
            "channels": {
                "sms": True,
                "viber": self.enable_viber,
                "whatsapp": self.enable_whatsapp,
                "rcs": self.enable_rcs,
            },
            "api_version": "2.0 Advanced",
        }
