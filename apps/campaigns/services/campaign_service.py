import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.campaigns import choices
from apps.partners import services as partner_services

logger = logging.getLogger(__name__)


class CampaignExecutionService:
    """Service for handling campaign execution logic."""

    @classmethod
    def can_execute_campaign(cls, campaign) -> bool:
        """
        Check if a campaign can be executed now.

        Args:
            campaign: Campaign instance

        Returns:
            bool: True if campaign can be executed
        """
        valid_statuses = [
            choices.CampaignStatus.ACTIVE,
            choices.CampaignStatus.SCHEDULED,
        ]
        return (
            campaign.status in valid_statuses
            and not campaign.is_processing
            and campaign.execution_date is not None
            and campaign.group is not None
        )

    @classmethod
    def start_campaign_execution(cls, campaign) -> bool:
        """
        Mark campaign as being processed and transition to PROCESSING state.

        This method ensures atomic execution through database-level locking.

        Args:
            campaign: Campaign instance

        Returns:
            bool: True if execution lock was acquired, False otherwise
        """
        with transaction.atomic():
            # Use select_for_update to ensure atomic read-modify-write
            from apps.campaigns.models import Campaign

            locked_campaign = Campaign.objects.select_for_update().get(
                pk=campaign.pk
            )

            if locked_campaign.is_processing:
                logger.warning(
                    f"Campaign {locked_campaign.id} is already being processed. "
                    f"Cannot acquire execution lock."
                )
                return False

            # Store original status for later reference
            original_status = locked_campaign.status

            # Update execution tracking fields
            locked_campaign.is_processing = True
            locked_campaign.last_execution_at = timezone.now()
            locked_campaign.execution_count += 1
            locked_campaign.status = choices.CampaignStatus.PROCESSING

            locked_campaign.save(
                update_fields=[
                    "is_processing",
                    "last_execution_at",
                    "execution_count",
                    "status",
                ]
            )

            logger.info(
                f"Campaign {locked_campaign.id} '{locked_campaign.name}' status changed: "
                f"{original_status} → PROCESSING (execution #{locked_campaign.execution_count})"
            )

            # Update the current instance to reflect changes
            campaign.is_processing = True
            campaign.last_execution_at = locked_campaign.last_execution_at
            campaign.execution_count = locked_campaign.execution_count
            campaign.status = locked_campaign.status
            campaign._original_status = original_status

            return True

    @classmethod
    def finish_campaign_execution(
        cls,
        campaign,
        success: bool = True,
        result_message: Optional[str] = None,
    ) -> None:
        """
        Mark campaign execution as finished and transition to appropriate status.

        Flow after processing:
        - Success + notifications created → SENDING (ready to send notifications)
        - Success + no notifications → Return to original status
        - Success + all sent → COMPLETED
        - Failure → FAILED

        Args:
            campaign: Campaign instance
            success: Whether execution was successful
            result_message: Optional result message
        """
        campaign.is_processing = False
        campaign.last_execution_result = result_message or (
            "Success" if success else "Failed"
        )

        update_fields = ["is_processing", "last_execution_result"]
        original_status = getattr(
            campaign,
            "_original_status",
            choices.CampaignStatus.DRAFT,
        )
        old_status = campaign.status

        if success:
            summary = CampaignNotificationService.get_notification_summary(
                campaign
            )

            if summary["total_notifications"] > 0:
                if cls._should_be_completed(campaign, summary):
                    # All notifications processed and at least some were sent
                    campaign.status = choices.CampaignStatus.COMPLETED
                    logger.info(
                        f"Campaign {campaign.id} completed: "
                        f"{summary['sent_notifications']} sent, "
                        f"{summary['failed_notifications']} failed"
                    )
                else:
                    # Notifications created and ready to be sent
                    campaign.status = choices.CampaignStatus.SENDING
                    logger.info(
                        f"Campaign {campaign.id} ready to send: "
                        f"{summary['total_notifications']} notifications created, "
                        f"{summary['pending_notifications']} pending"
                    )
            else:
                # No notifications created - return to previous status
                if original_status == choices.CampaignStatus.SCHEDULED:
                    campaign.status = choices.CampaignStatus.SCHEDULED
                else:
                    campaign.status = choices.CampaignStatus.ACTIVE

                logger.warning(
                    f"Campaign {campaign.id} processing completed but no notifications created. "
                    f"Returning to {campaign.get_status_display()} status."
                )

            update_fields.append("status")
        else:
            # Execution failed - transition to FAILED
            campaign.status = choices.CampaignStatus.FAILED
            update_fields.append("status")
            logger.error(
                f"Campaign {campaign.id} execution failed: {result_message}"
            )

        if old_status != campaign.status:
            logger.info(
                f"Campaign {campaign.id} '{campaign.name}' status changed: "
                f"{old_status} → {campaign.status}"
            )

        campaign.save(update_fields=update_fields)

    @classmethod
    def _should_be_completed(cls, campaign, summary: Dict[str, int]) -> bool:
        """
        Check if campaign should be marked as completed based on notification status.

        Args:
            campaign: Campaign instance
            summary: Notification summary dictionary

        Returns:
            bool: True if campaign should be completed
        """
        return (
            summary["total_notifications"] > 0
            and summary["pending_notifications"] == 0
            and summary["sent_notifications"] > 0
        )


class CampaignNotificationService:
    """Service for handling campaign notification operations."""

    @classmethod
    def create_notifications_for_partners(
        cls, campaign, notification_type: str, partners: Optional[List] = None
    ) -> List:
        """
        Create notifications for specified partners or all partners in the group.

        Args:
            campaign: Campaign instance
            notification_type: Type of notification to create
            partners: Optional list of partners, defaults to all in group

        Returns:
            List of created notification instances
        """
        from django.contrib.contenttypes.models import ContentType

        from apps.notifications.models import CampaignNotification

        if not campaign.group:
            return []

        if partners is None:
            partners = campaign.group.partners.all()

        if not partners:
            return []

        # Get ContentType instances for the generic foreign keys
        campaign_content_type = ContentType.objects.get_for_model(campaign)
        # Get ContentType for Partner model
        from apps.partners.models import Partner

        partner_content_type = ContentType.objects.get_for_model(Partner)

        notifications = []
        for partner in partners:
            partner_debt = partner_services.PartnerDebtService.get_single_partner_debt_detail(
                partner
            )

            notification = CampaignNotification(
                campaign_type=campaign_content_type,
                campaign_id=campaign.id,
                recipient_type=partner_content_type,
                recipient_id=partner.id,
                notification_type=notification_type,
                channel=choices.NotificationChannel.WHATSAPP,  # Default channel
                recipient_email=partner.email,
                recipient_phone=partner.phone,
                total_debt_amount=partner_debt["total_debt"],
                included_payment_link=campaign.use_payment_link,
                created_by=campaign.created_by,
                modified_by=campaign.modified_by,
            )
            notifications.append(notification)

        # Bulk create notifications
        if notifications:
            CampaignNotification.objects.bulk_create(notifications)

        return notifications

    @classmethod
    def get_notification_summary(cls, campaign) -> Dict[str, int]:
        """
        Get summary of notifications for a campaign.

        Args:
            campaign: Campaign instance

        Returns:
            Dict with notification counts by status
        """
        from django.contrib.contenttypes.models import ContentType

        from apps.notifications.models import CampaignNotification

        # Get the ContentType for the campaign model
        campaign_content_type = ContentType.objects.get_for_model(campaign)

        # Query notifications using GenericForeignKey fields
        notifications_queryset = CampaignNotification.objects.filter(
            campaign_type=campaign_content_type, campaign_id=campaign.id
        )

        summary = notifications_queryset.aggregate(
            total=Count("id"),
            pending=Count(
                "id",
                filter=Q(status=choices.NotificationStatus.PENDING),
            ),
            sent=Count(
                "id",
                filter=Q(status=choices.NotificationStatus.SENT),
            ),
            failed=Count(
                "id",
                filter=Q(status=choices.NotificationStatus.FAILED),
            ),
            cancelled=Count(
                "id",
                filter=Q(status=choices.NotificationStatus.CANCELLED),
            ),
        )

        return {
            "total_notifications": summary["total"] or 0,
            "pending_notifications": summary["pending"] or 0,
            "sent_notifications": summary["sent"] or 0,
            "failed_notifications": summary["failed"] or 0,
            "cancelled_notifications": summary["cancelled"] or 0,
        }

    @classmethod
    def calculate_notification_progress_percentage(cls, campaign) -> float:
        """
        Calculate the percentage of notifications that have been processed.

        Args:
            campaign: Campaign instance

        Returns:
            float: Progress percentage (0-100)
        """
        summary = cls.get_notification_summary(campaign)
        total = summary["total_notifications"]

        if total == 0:
            return 100.0

        processed = (
            summary["sent_notifications"]
            + summary["failed_notifications"]
            + summary["cancelled_notifications"]
        )
        return round((processed / total) * 100, 2)


class CampaignStatusService:
    """Service for handling campaign status flow and transitions."""

    @classmethod
    def get_status_flow_info(cls) -> Dict[str, Any]:
        """
        Get information about the campaign status flow and transitions.

        Returns:
            dict: Information about status flow, valid transitions, and descriptions
        """
        return {
            "flow": {
                "description": "Campaign lifecycle status flow",
                "stages": [
                    {
                        "status": choices.CampaignStatus.DRAFT,
                        "label": "Draft",
                        "description": "Campaign is being configured",
                        "next_states": [
                            choices.CampaignStatus.SCHEDULED,
                            choices.CampaignStatus.ACTIVE,
                            choices.CampaignStatus.CANCELLED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.SCHEDULED,
                        "label": "Scheduled",
                        "description": "Campaign is scheduled for future execution",
                        "next_states": [
                            choices.CampaignStatus.PROCESSING,
                            choices.CampaignStatus.CANCELLED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.PROCESSING,
                        "label": "Processing",
                        "description": "Creating notifications for campaign partners",
                        "next_states": [
                            choices.CampaignStatus.SENDING,
                            choices.CampaignStatus.ACTIVE,
                            choices.CampaignStatus.FAILED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.SENDING,
                        "label": "Sending",
                        "description": "Notifications are being sent to partners",
                        "next_states": [
                            choices.CampaignStatus.COMPLETED,
                            choices.CampaignStatus.FAILED,
                            choices.CampaignStatus.PAUSED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.ACTIVE,
                        "label": "Active",
                        "description": "Campaign is active and can send notifications",
                        "next_states": [
                            choices.CampaignStatus.SENDING,
                            choices.CampaignStatus.COMPLETED,
                            choices.CampaignStatus.PAUSED,
                            choices.CampaignStatus.CANCELLED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.PAUSED,
                        "label": "Paused",
                        "description": "Campaign is temporarily paused",
                        "next_states": [
                            choices.CampaignStatus.ACTIVE,
                            choices.CampaignStatus.CANCELLED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.COMPLETED,
                        "label": "Completed",
                        "description": "All notifications have been processed",
                        "next_states": [],
                    },
                    {
                        "status": choices.CampaignStatus.FAILED,
                        "label": "Failed",
                        "description": "Campaign execution failed",
                        "next_states": [
                            choices.CampaignStatus.DRAFT,
                            choices.CampaignStatus.SCHEDULED,
                        ],
                    },
                    {
                        "status": choices.CampaignStatus.CANCELLED,
                        "label": "Cancelled",
                        "description": "Campaign was cancelled",
                        "next_states": [],
                    },
                ],
            },
            "main_flow": "DRAFT → SCHEDULED → PROCESSING → SENDING → COMPLETED",
            "error_flow": "Any state → FAILED → (Manual fix) → DRAFT/SCHEDULED",
        }

    @classmethod
    def get_current_status_info(cls, campaign) -> Dict[str, Any]:
        """
        Get information about the current status and possible next states.

        Args:
            campaign: Campaign instance

        Returns:
            Dict with current status information
        """
        flow_info = cls.get_status_flow_info()
        current_stage = next(
            (
                stage
                for stage in flow_info["flow"]["stages"]
                if stage["status"] == campaign.status
            ),
            None,
        )

        summary = CampaignNotificationService.get_notification_summary(campaign)

        return {
            "current_status": campaign.status,
            "current_status_display": campaign.get_status_display(),
            "description": current_stage["description"]
            if current_stage
            else "",
            "next_possible_states": (
                current_stage["next_states"] if current_stage else []
            ),
            "is_processing": campaign.is_processing,
            "execution_count": campaign.execution_count,
            "last_execution_at": campaign.last_execution_at,
            "notification_summary": summary,
            "progress_percentage": CampaignNotificationService.calculate_notification_progress_percentage(
                campaign
            ),
        }


class MessageTemplateService:
    """Service for handling message template operations."""

    @classmethod
    def render_template_message(cls, template, context: Dict[str, Any]) -> str:
        """
        Render a message template with provided context.

        Args:
            template: MessageTemplate instance
            context: Dictionary with values for template placeholders

        Returns:
            str: Rendered message with placeholders replaced
        """
        message = template.message_body
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        return message

    @classmethod
    def get_template_context_for_partner(
        cls, partner, campaign
    ) -> Dict[str, Any]:
        """
        Generate template context for a specific partner and campaign.

        Args:
            partner: Partner instance
            campaign: Campaign instance

        Returns:
            Dict with template context variables
        """
        partner_debt = (
            partner_services.PartnerDebtService.get_single_partner_debt_detail(
                partner
            )
        )

        return {
            "partner_name": partner.full_name,
            "debt_amount": partner_debt.get("total_debt", Decimal("0.00")),
            "company_name": "Xofi",  # This could come from settings
            "contact_phone": "+57 300 123 4567",  # This could come from settings
            "due_date": "Próximo vencimiento",  # This would need to be calculated
            "payment_link": "#",  # This would be generated if needed
        }
