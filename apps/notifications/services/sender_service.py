import logging
from typing import Dict, Optional

from apps.campaigns import choices
from apps.campaigns import models as campaign_models
from apps.campaigns.utils import messages as message_utils
from apps.notifications import models
from apps.notifications.providers.factory import ProviderFactory
from apps.partners import models as partner_models
from apps.partners import services as partner_services

logger = logging.getLogger(__name__)


class NotificationSenderService:
    """Service for sending individual notifications."""

    @classmethod
    def send_notification(cls, notification) -> Dict[str, any]:
        """
        Send a notification through the appropriate provider.

        Args:
            notification: CampaignNotification instance

        Returns:
            dict: Result with success status and details
        """
        # Get the appropriate provider for the channel
        provider = ProviderFactory.get_provider(notification.channel)
        channel_name = notification.get_channel_display()

        if not provider:
            error_msg = f"No provider available for channel: {channel_name}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        # Check if provider is configured
        if not provider.is_configured():
            error_msg = f"{channel_name} provider is not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        # Prepare message and get template
        message_result = cls._prepare_message(notification)
        if not message_result["success"]:
            return message_result

        message_content = message_result["message"]
        recipient = message_result["recipient"]

        # Fetch template: Priority 1: Campaign specific template, Priority 2: Channel default
        template = getattr(notification.campaign, "message_template", None)

        # Send message
        try:
            # Check if we should use WhatsApp Template (Official API)
            if (
                notification.channel == choices.NotificationChannel.WHATSAPP
                and template
                and template.whatsapp_template_name
            ):
                debt_detail = cls._get_debt_detail(notification)
                context = message_utils.prepare_message_context(
                    notification, debt_detail
                )
                components = template.get_whatsapp_components(context)

                result = provider.send_template_message(
                    recipient=recipient,
                    template_name=template.whatsapp_template_name,
                    components=components,
                )
            elif (
                notification.included_payment_link
                and notification.payment_link_url
            ):
                # Send with payment button
                result = provider.send_message_with_button(
                    recipient=recipient,
                    message=message_content,
                    button_text="Pagar ahora",
                    button_url=notification.payment_link_url,
                )
            else:
                # Send plain text message
                result = provider.send_text_message(
                    recipient=recipient, message=message_content
                )

            if result.get("success"):
                logger.info(
                    f"Notification {notification.id} sent successfully "
                    f"via {notification.get_channel_display()}"
                )

            return result

        except Exception as e:
            error_msg = f"Error sending notification: {str(e)}"
            logger.exception(error_msg)
            return {"success": False, "error": error_msg}

    @classmethod
    def _prepare_message(cls, notification) -> Dict[str, any]:
        """
        Prepare the message content for a notification.

        Args:
            notification: CampaignNotification instance

        Returns:
            dict: Result with message and recipient
        """
        # Get recipient identifier
        recipient = cls._get_recipient_identifier(notification)
        if not recipient:
            return {
                "success": False,
                "error": f"No {notification.get_channel_display()} identifier found",
            }

        # Check if message is already prepared
        if notification.message_content:
            return {
                "success": True,
                "message": notification.message_content,
                "recipient": recipient,
            }

        # Generate message content
        try:
            message_content = cls._generate_message_content(notification)

            # Store the message content
            notification.message_content = message_content
            notification.save(update_fields=["message_content"])

            return {
                "success": True,
                "message": message_content,
                "recipient": recipient,
            }

        except Exception as e:
            error_msg = f"Error generating message: {str(e)}"
            logger.exception(error_msg)
            return {"success": False, "error": error_msg}

    @classmethod
    def _get_recipient_identifier(cls, notification) -> Optional[str]:
        """
        Get the recipient identifier for the notification channel.

        Args:
            notification: CampaignNotification instance

        Returns:
            str: Recipient identifier or None
        """
        channel = notification.channel

        if channel == choices.NotificationChannel.WHATSAPP:
            return notification.recipient_phone
        elif channel == choices.NotificationChannel.TELEGRAM:
            return notification.recipient_telegram_id
        elif channel == choices.NotificationChannel.EMAIL:
            return notification.recipient_email
        elif channel == choices.NotificationChannel.SMS:
            return notification.recipient_phone

        return None

    @classmethod
    def _generate_message_content(cls, notification) -> str:
        """
        Generate message content from template or default.

        Args:
            notification: CampaignNotification instance

        Returns:
            str: Generated message content
        """
        template = getattr(notification.campaign, "message_template", None)

        if not template:
            try:
                template = models.MessageTemplate.objects.get(
                    template_type=notification.notification_type,
                    channel=notification.channel,
                    is_active=True,
                )
            except models.MessageTemplate.DoesNotExist:
                template = None

        debt_detail = cls._get_debt_detail(notification)

        context = message_utils.prepare_message_context(
            notification, debt_detail
        )

        if template:
            message = template.render_message(context)
        else:
            message = message_utils.generate_default_message(
                notification, context, debt_detail
            )

        return message

    @classmethod
    def _get_debt_detail(cls, notification) -> Dict:
        """
        Get debt detail for notification recipient.

        Args:
            notification: CampaignNotification instance

        Returns:
            dict: Debt detail information
        """

        recipient = notification.recipient

        if isinstance(recipient, partner_models.Partner):
            return partner_services.PartnerDebtService.get_single_partner_debt_detail(
                recipient
            )
        elif isinstance(recipient, campaign_models.CSVContact):
            return {
                "total_debt": recipient.amount,
                "credit_debt": 0,
                "contribution_debt": 0,
                "social_security_debt": 0,
                "penalty_debt": 0,
                "overdue_installments": [],
                "overdue_contributions": [],
                "overdue_social_security": [],
                "overdue_penalties": [],
            }

        return {
            "total_debt": notification.total_debt_amount or 0,
            "credit_debt": 0,
            "contribution_debt": 0,
            "social_security_debt": 0,
            "penalty_debt": 0,
            "overdue_installments": [],
            "overdue_contributions": [],
            "overdue_social_security": [],
            "overdue_penalties": [],
        }
