import logging

from celery import shared_task
from django.utils import timezone

from apps.campaigns import choices as notifications_choices
from apps.campaigns import models as campaign_models
from apps.notifications import choices as notification_choices
from apps.notifications import models
from apps.notifications.services import (
    NotificationSenderService,
    NotificationService,
)

logger = logging.getLogger(__name__)


@shared_task(name="notifications.process_campaign_notifications")
def process_campaign_notifications(
    campaign_id: int, campaign_type: str = "GROUP"
) -> dict:
    """
    Process and schedule notifications for a campaign.

    This task creates notification records for campaigns (both group and file-based).

    Args:
        campaign_id: ID of the campaign to process
        campaign_type: Type of campaign ('GROUP' or 'FILE')

    Returns:
        dict: Summary of created notifications
    """
    logger.info(
        f"Starting to process {campaign_type} campaign notifications for campaign {campaign_id}"
    )

    try:
        # Get the appropriate campaign model
        if campaign_type == "FILE":
            campaign = campaign_models.CampaignCSVFile.objects.get(
                id=campaign_id
            )
        else:
            campaign = campaign_models.Campaign.objects.select_related(
                "group"
            ).get(id=campaign_id)

        logger.info(
            f"Campaign found: '{campaign.name}' "
            f"(Type: {campaign_type}, Status: {campaign.get_status_display()})"
        )
    except Exception:
        logger.error(
            f"{campaign_type.capitalize()} campaign {campaign_id} not found"
        )
        return {"success": False, "error": "Campaign not found"}

    # Execute campaign using the notification service
    result = NotificationService.execute_campaign(campaign)

    logger.info(
        f"Campaign {campaign_id} processing finished - Success: {result.get('success')}. "
        f"Message: {result.get('message', 'N/A')}"
    )

    return result


@shared_task(name="notifications.send_scheduled_notifications")
def send_scheduled_notifications() -> dict:
    """
    Send all pending notifications that are scheduled to be sent now.

    This task should be run periodically (e.g., every 5-10 minutes) to check
    for notifications that need to be sent.

    When notifications are found, the campaign status is transitioned to SENDING
    if it's not already in that state.

    Returns:
        dict: Summary of sent notifications
    """
    logger.info("Starting scheduled notifications processing")
    now = timezone.now()
    logger.info(f"Current time: {now}")

    # Get all pending notifications scheduled for now or earlier
    pending_notifications = models.CampaignNotification.objects.filter(
        status=notifications_choices.NotificationStatus.PENDING,
        scheduled_at__lte=now,
    ).select_related("campaign_type", "recipient_type")

    total_pending = pending_notifications.count()
    logger.info(
        f"Found {total_pending} pending notifications scheduled for now or earlier"
    )

    if total_pending == 0:
        logger.info("No pending notifications to process")
        return {
            "success": True,
            "queued_count": 0,
            "failed_count": 0,
            "cancelled_count": 0,
        }

    sent_count = 0
    failed_count = 0
    cancelled_count = 0

    # Track campaigns that need status update to SENDING
    campaigns_to_update = set()

    for notification in pending_notifications:
        try:
            campaign = notification.campaign
            recipient_name = getattr(
                notification.recipient, "full_name", "Unknown"
            )
            campaign_name = getattr(campaign, "name", "Unknown")

            logger.info(
                f"Processing notification {notification.id} for recipient '{recipient_name}' "
                f"from campaign '{campaign_name}'"
            )

            # Check if campaign can send notifications
            valid_sending_statuses = [
                notifications_choices.CampaignStatus.ACTIVE,
                notifications_choices.CampaignStatus.SENDING,
            ]

            if campaign.status not in valid_sending_statuses:
                logger.info(
                    f"Cancelling notification {notification.id} - campaign '{campaign_name}' "
                    f"cannot send notifications (status: {campaign.get_status_display()})"
                )
                notification.status = (
                    notifications_choices.NotificationStatus.CANCELLED
                )
                notification.save(update_fields=["status"])
                cancelled_count += 1
                continue

            # Transition campaign to SENDING if it's ACTIVE
            if campaign.status == notifications_choices.CampaignStatus.ACTIVE:
                campaigns_to_update.add(
                    (campaign.id, notification.campaign_type.model)
                )

            # Send notification asynchronously
            try:
                send_notification.delay(notification.id)
                sent_count += 1
                logger.info(
                    f"Successfully queued notification {notification.id} for sending"
                )
            except Exception as e:
                logger.error(
                    f"Failed to queue notification {notification.id}: {e}"
                )
                failed_count += 1

        except Exception as e:
            logger.error(
                f"Error processing notification {notification.id}: {e}",
                exc_info=True,
            )
            failed_count += 1

    # Update campaign statuses to SENDING
    if campaigns_to_update:
        for campaign_id, model_type in campaigns_to_update:
            try:
                if model_type == "campaign":
                    campaign_models.Campaign.objects.filter(
                        id=campaign_id,
                        status=notifications_choices.CampaignStatus.ACTIVE,
                    ).update(
                        status=notifications_choices.CampaignStatus.SENDING
                    )
                elif model_type == "campaigncsvfile":
                    campaign_models.CampaignCSVFile.objects.filter(
                        id=campaign_id,
                        status=notifications_choices.CampaignStatus.ACTIVE,
                    ).update(
                        status=notifications_choices.CampaignStatus.SENDING
                    )
            except Exception as e:
                logger.error(
                    f"Error updating campaign {campaign_id} status: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Processed {len(campaigns_to_update)} campaign status transitions"
        )

    logger.info(
        f"Scheduled notifications processing completed: "
        f"Queued {sent_count} notifications for sending, "
        f"Failed to queue {failed_count}, "
        f"Cancelled {cancelled_count} (inactive campaigns)"
    )

    return {
        "success": True,
        "queued_count": sent_count,
        "failed_count": failed_count,
        "cancelled_count": cancelled_count,
    }


@shared_task(
    name="notifications.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_notification(self, notification_id: int) -> dict:
    """
    Send a notification for a campaign with WhatsApp rate limiting.

    Uses NotificationSenderService for sending messages via different channels.
    For WhatsApp, applies rate limiting to comply with WHAPI best practices.

    Args:
        notification_id: ID of the CampaignNotification to send

    Returns:
        dict: Result with success status and details
    """
    try:
        notification = models.CampaignNotification.objects.select_related(
            "campaign_type", "recipient_type"
        ).get(id=notification_id)
    except models.CampaignNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {"success": False, "error": "Notification not found"}

    # Check WhatsApp rate limits before sending
    if notification.channel == notification_choices.NotificationChannel.WHATSAPP:
        from apps.notifications.services.whatsapp_rate_limiter import (
            WhatsAppRateLimiter,
        )

        rate_check = WhatsAppRateLimiter.can_send_message()
        if not rate_check.get("allowed"):
            wait_seconds = rate_check.get("wait_seconds", 60)
            reason = rate_check.get("reason", "Rate limit exceeded")
            logger.warning(
                f"WhatsApp rate limit reached for notification {notification_id}: {reason}. "
                f"Retrying in {wait_seconds} seconds."
            )
            # Retry after the wait period
            raise self.retry(countdown=wait_seconds)

    # Increment attempt counter
    notification.increment_attempt()

    logger.info(
        f"Sending notification {notification_id} via {notification.get_channel_display()}"
    )

    # Send notification using the service
    try:
        result = NotificationSenderService.send_notification(notification)

        if result.get("success"):
            notification.mark_as_sent()
            logger.info(
                f"Notification {notification_id} sent successfully "
                f"via {notification.get_channel_display()}"
            )
            return {
                "success": True,
                "notification_id": notification_id,
                "response": result.get("response"),
            }
        else:
            error_msg = result.get("error", "Unknown error")
            notification.mark_as_failed(error_msg)
            logger.exception(
                f"Failed to send notification {notification_id}: {error_msg}"
            )

            # Retry on failure
            raise self.retry(exc=Exception(error_msg))

    except Exception as exc:
        error_msg = str(exc)
        notification.mark_as_failed(error_msg)
        logger.exception(f"Exception sending notification {notification_id}")

        # Retry
        raise self.retry(exc=exc)
