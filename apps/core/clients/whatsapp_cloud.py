import hashlib
import hmac
import logging
from typing import Any

from decouple import config

from apps.core.clients.base import BaseAPIClient
from apps.core.clients.exceptions import APIClientError, APIValidationError

logger = logging.getLogger(__name__)

DEFAULT_API_VERSION = "v21.0"
GRAPH_API_BASE_URL = "https://graph.facebook.com"


class WhatsAppCloudAPIClient(BaseAPIClient):
    """
    Official WhatsApp Cloud API client (Meta / graph.facebook.com).

    Authentication uses a permanent System User Access Token sent as
    a Bearer token in the Authorization header.

    Supports:
    - Sending text messages
    - Sending template messages (required for business-initiated notifications)
    - Sending media messages (image, video, document)
    - Webhook verification (GET challenge)
    - Webhook payload signature validation (HMAC-SHA256 with App Secret)

    Environment variables:
    - WHATSAPP_CLOUD_PHONE_NUMBER_ID: Phone number ID from Meta Business Manager
    - WHATSAPP_CLOUD_ACCESS_TOKEN: Permanent system user access token
    - WHATSAPP_CLOUD_VERIFY_TOKEN: User-defined webhook verification token
    - WHATSAPP_CLOUD_APP_SECRET: Facebook App Secret for signature validation
    - WHATSAPP_CLOUD_API_VERSION: Graph API version (default: v21.0)
    """

    def __init__(
        self,
        phone_number_id: str | None = None,
        access_token: str | None = None,
        verify_token: str | None = None,
        app_secret: str | None = None,
        api_version: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        """
        Initialize WhatsApp Cloud API client.

        Args:
            phone_number_id: Phone number ID from Meta Business Manager.
            access_token: Permanent system user access token.
            verify_token: User-defined token for webhook verification.
            app_secret: Facebook App Secret for HMAC-SHA256 signature validation.
            api_version: Graph API version (default: v21.0).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
        """
        self.phone_number_id = phone_number_id or config(
            "WHATSAPP_CLOUD_PHONE_NUMBER_ID", default=""
        )
        access_token = access_token or config(
            "WHATSAPP_CLOUD_ACCESS_TOKEN", default=""
        )
        self.verify_token = verify_token or config(
            "WHATSAPP_CLOUD_VERIFY_TOKEN", default=""
        )
        self.app_secret = app_secret or config(
            "WHATSAPP_CLOUD_APP_SECRET", default=""
        )
        api_version = api_version or config(
            "WHATSAPP_CLOUD_API_VERSION", default=DEFAULT_API_VERSION
        )
        timeout = timeout or config("WHATSAPP_TIMEOUT", default=30, cast=int)
        max_retries = max_retries or config(
            "WHATSAPP_MAX_RETRIES", default=3, cast=int
        )

        base_url = f"{GRAPH_API_BASE_URL}/{api_version}"

        super().__init__(
            base_url=base_url,
            api_key=access_token,
            timeout=timeout,
            max_retries=max_retries,
        )

    def send_message(self, to: str, message: str) -> dict[str, Any]:
        """
        Send a text message via WhatsApp Cloud API.

        Args:
            to: Recipient phone number in E.164 format (e.g. '+51999999999').
            message: Text content to send.

        Returns:
            dict: API response with 'messages' array containing message IDs.

        Raises:
            APIValidationError: If required fields are missing.
            APIClientError: If the API request fails.
        """
        if not to:
            raise APIValidationError("Recipient phone number (to) is required")
        if not message:
            raise APIValidationError("Message text is required")

        phone = self._normalize_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        logger.info(
            "Sending WhatsApp Cloud API text message to %s (%d chars)",
            phone,
            len(message),
        )

        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload,
            )
            message_id = self._extract_message_id(response)
            logger.info("Message sent successfully: %s", message_id)
            return response
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error sending message: %s", exc)
            raise APIClientError(f"Failed to send message: {exc}") from exc

    def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "es",
        components: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Send a template message via WhatsApp Cloud API.

        Template messages are required for business-initiated conversations
        (outside the 24-hour customer service window). Templates must be
        pre-approved in Meta Business Manager.

        Args:
            to: Recipient phone number in E.164 format.
            template_name: Name of the approved message template.
            language: Template language code (default: 'es').
            components: Optional list of template component parameters
                        (header, body, button variables).

        Returns:
            dict: API response with 'messages' array containing message IDs.

        Raises:
            APIValidationError: If required fields are missing.
            APIClientError: If the API request fails.
        """
        if not to:
            raise APIValidationError("Recipient phone number (to) is required")
        if not template_name:
            raise APIValidationError("Template name is required")

        phone = self._normalize_phone(to)

        template_data: dict[str, Any] = {
            "name": template_name,
            "language": {"code": language},
        }
        if components:
            template_data["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "template",
            "template": template_data,
        }

        logger.info(
            "Sending WhatsApp Cloud API template '%s' to %s",
            template_name,
            phone,
        )

        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload,
            )
            message_id = self._extract_message_id(response)
            logger.info("Template message sent successfully: %s", message_id)
            return response
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error sending template: %s", exc)
            raise APIClientError(f"Failed to send template: {exc}") from exc

    def send_media(
        self,
        to: str,
        media_url: str,
        caption: str = "",
        media_type: str = "image",
    ) -> dict[str, Any]:
        """
        Send a media message (image, video, document) via WhatsApp Cloud API.

        Args:
            to: Recipient phone number in E.164 format.
            media_url: Public HTTPS URL pointing to the media file.
            caption: Optional caption text.
            media_type: Type of media ('image', 'video', 'document', 'audio').

        Returns:
            dict: API response with 'messages' array containing message IDs.

        Raises:
            APIValidationError: If required fields are missing.
            APIClientError: If the API request fails.
        """
        if not to:
            raise APIValidationError("Recipient phone number (to) is required")
        if not media_url:
            raise APIValidationError("Media URL is required")

        phone = self._normalize_phone(to)

        media_types_map = {
            "image": "image",
            "video": "video",
            "document": "document",
            "audio": "audio",
            "photo": "image",
        }
        wa_media_type = media_types_map.get(media_type, "document")

        media_object: dict[str, Any] = {"link": media_url}
        if caption and wa_media_type in ("image", "video", "document"):
            media_object["caption"] = caption
        if wa_media_type == "document" and not caption:
            media_object["filename"] = media_url.split("/")[-1] or "file"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": wa_media_type,
            wa_media_type: media_object,
        }

        logger.info(
            "Sending WhatsApp Cloud API media (%s) to %s: %s",
            wa_media_type,
            phone,
            media_url,
        )

        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload,
            )
            message_id = self._extract_message_id(response)
            logger.info("Media sent successfully: %s", message_id)
            return response
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error sending media: %s", exc)
            raise APIClientError(f"Failed to send media: {exc}") from exc

    def send_interactive(self, to: str, interactive_data: dict) -> dict[str, Any]:
        """
        Send an interactive message (List or Buttons) via WhatsApp Cloud API.

        Args:
            to: Recipient phone number in E.164 format.
            interactive_data: Dictionary containing the interactive message structure.

        Returns:
            dict: API response.

        Raises:
            APIValidationError: If required fields are missing.
            APIClientError: If the API request fails.
        """
        if not to:
            raise APIValidationError("Recipient phone number (to) is required")
        if not interactive_data:
            raise APIValidationError("Interactive data is required")

        phone = self._normalize_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "interactive",
            "interactive": interactive_data,
        }

        logger.info("Sending WhatsApp Cloud API interactive message to %s", phone)

        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload,
            )
            message_id = self._extract_message_id(response)
            logger.info("Interactive message sent successfully: %s", message_id)
            return response
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error sending interactive message: %s", exc)
            raise APIClientError(f"Failed to send interactive message: {exc}") from exc

    def verify_webhook_challenge(
        self, mode: str, token: str, challenge: str
    ) -> str | None:
        """
        Handle the webhook verification GET request from Meta.

        When configuring a webhook URL, Meta sends a GET request with:
        - hub.mode = 'subscribe'
        - hub.verify_token = the token you configured
        - hub.challenge = a random string to echo back

        Args:
            mode: Value of 'hub.mode' query parameter.
            token: Value of 'hub.verify_token' query parameter.
            challenge: Value of 'hub.challenge' query parameter.

        Returns:
            str: The challenge string if verification succeeds.
            None: If verification fails.
        """
        if mode != "subscribe":
            logger.warning(
                "Webhook verification failed: mode is '%s', expected 'subscribe'",
                mode,
            )
            return None

        if not self.verify_token:
            logger.warning(
                "WHATSAPP_VERIFY_TOKEN not configured; cannot verify webhook"
            )
            return None

        if not hmac.compare_digest(token, self.verify_token):
            logger.warning("Webhook verification failed: invalid verify_token")
            return None

        logger.info("Webhook verification successful")
        return challenge

    def verify_webhook_signature(
        self, payload: bytes, signature_header: str
    ) -> bool:
        """
        Validate the X-Hub-Signature-256 header of an incoming webhook POST.

        Meta signs each webhook payload using HMAC-SHA256 with the App Secret.
        The header format is: 'sha256={hex_digest}'.

        Args:
            payload: Raw request body as bytes.
            signature_header: Value of the X-Hub-Signature-256 header.

        Returns:
            bool: True if the signature is valid.
        """
        if not self.app_secret:
            logger.debug(
                "WHATSAPP_APP_SECRET not configured; "
                "skipping signature validation"
            )
            return True

        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header")
            return False

        expected_signature = signature_header[7:]

        computed_signature = hmac.new(
            key=self.app_secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(computed_signature, expected_signature)

        if not is_valid:
            logger.warning(
                "WhatsApp Cloud API webhook signature validation failed"
            )

        return is_valid

    def mark_message_as_read(self, message_id: str) -> dict[str, Any]:
        """
        Mark a received message as read (sends blue checkmarks).

        Args:
            message_id: The wamid of the message to mark as read.

        Returns:
            dict: API response.

        Raises:
            APIClientError: If the API request fails.
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            return self._make_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload,
            )
        except Exception as exc:
            logger.error("Error marking message as read: %s", exc)
            raise APIClientError(
                f"Failed to mark message as read: {exc}"
            ) from exc

    def list_templates(self, waba_id: str) -> list[dict[str, Any]]:
        """
        List all WhatsApp Business Message Templates for a WABA.

        Calls Meta Graph API: GET /{waba_id}/message_templates
        Returns templates with their approval status (APPROVED, PENDING, REJECTED, etc.)

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            list: List of template dicts with name, status, category, language, components.

        Raises:
            APIClientError: If the API request fails.
        """
        if not waba_id:
            raise APIValidationError(
                "WhatsApp Business Account ID (waba_id) is required"
            )

        try:
            response = self._make_request(
                method="GET",
                endpoint=f"/{waba_id}/message_templates",
                params={
                    "fields": "name,status,category,language,components",
                    "limit": 100,
                },
            )
            templates = response.get("data", [])
            logger.info(
                "Fetched %d WhatsApp templates for WABA %s",
                len(templates),
                waba_id,
            )
            return templates
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error listing templates: %s", exc)
            raise APIClientError(f"Failed to list templates: {exc}") from exc

    def create_template(
        self,
        waba_id: str,
        name: str,
        category: str,
        language: str,
        body_text: str,
        header_text: str = "",
        footer_text: str = "",
    ) -> dict[str, Any]:
        """
        Create a new WhatsApp Business Message Template.

        Calls Meta Graph API: POST /{waba_id}/message_templates
        The template will be in PENDING status until Meta approves it.

        Args:
            waba_id: WhatsApp Business Account ID.
            name: Template name (lowercase, underscores only).
            category: Template category (MARKETING, UTILITY, AUTHENTICATION).
            language: Template language code (e.g. 'es', 'en_US').
            body_text: Main body text of the template.
            header_text: Optional header text.
            footer_text: Optional footer text.

        Returns:
            dict: API response with template id and status.

        Raises:
            APIValidationError: If required fields are missing.
            APIClientError: If the API request fails.
        """
        if not waba_id:
            raise APIValidationError("waba_id is required")
        if not name:
            raise APIValidationError("Template name is required")
        if not body_text:
            raise APIValidationError("Body text is required")

        components: list[dict[str, Any]] = []

        if header_text:
            components.append(
                {
                    "type": "HEADER",
                    "format": "TEXT",
                    "text": header_text,
                }
            )

        components.append(
            {
                "type": "BODY",
                "text": body_text,
            }
        )

        if footer_text:
            components.append(
                {
                    "type": "FOOTER",
                    "text": footer_text,
                }
            )

        payload = {
            "name": name,
            "category": category,
            "language": language,
            "components": components,
        }

        logger.info(
            "Creating WhatsApp template '%s' (category=%s, lang=%s)",
            name,
            category,
            language,
        )

        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/{waba_id}/message_templates",
                data=payload,
            )
            logger.info(
                "Template created: id=%s status=%s",
                response.get("id"),
                response.get("status"),
            )
            return response
        except APIClientError:
            raise
        except Exception as exc:
            logger.error("Unexpected error creating template: %s", exc)
            raise APIClientError(f"Failed to create template: {exc}") from exc

    def validate_api_key(self) -> bool:
        """
        Validate that the access token and phone number ID are working.

        Returns:
            bool: True if the credentials are valid.
        """
        if not self.phone_number_id or not self.api_key:
            logger.error(
                "WHATSAPP_PHONE_NUMBER_ID or "
                "WHATSAPP_ACCESS_TOKEN is not configured"
            )
            return False

        try:
            response = self._make_request(
                method="GET",
                endpoint=f"/{self.phone_number_id}",
            )
            is_valid = bool(response.get("id"))
            if not is_valid:
                logger.warning(
                    "WhatsApp Cloud API validation failed: no ID in response"
                )
            return is_valid
        except APIClientError as exc:
            logger.error("API key validation failed: %s", exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error during API key validation: %s", exc)
            return False

    def health_check(self) -> bool:
        """
        Check if the WhatsApp Cloud API is reachable.

        Returns:
            bool: True if the API is accessible.
        """
        try:
            self._make_request(
                method="GET",
                endpoint=f"/{self.phone_number_id}",
            )
            return True
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return False

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        Normalize phone number for WhatsApp Cloud API.

        The Cloud API expects phone numbers without the '+' prefix
        and without any formatting characters.

        Args:
            phone: Phone number in E.164 format or Green API chatId format.

        Returns:
            str: Normalized phone number (digits only).
        """
        # Strip Green API chatId suffix
        if "@" in phone:
            phone = phone.split("@")[0]

        # Remove '+' prefix and whitespace
        return phone.lstrip("+").replace(" ", "").replace("-", "")

    @staticmethod
    def _extract_message_id(response: dict[str, Any]) -> str:
        """
        Extract the message ID from a Cloud API send response.

        Args:
            response: API response dictionary.

        Returns:
            str: Message ID (wamid), or 'unknown' if not found.
        """
        messages = response.get("messages", [])
        if messages:
            return messages[0].get("id", "unknown")
        return "unknown"
