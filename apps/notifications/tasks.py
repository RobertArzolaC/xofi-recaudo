import logging

from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from apps.campaigns import choices as campaigns_choices
from apps.campaigns import models as campaign_models
from apps.notifications import choices as notification_choices
from apps.notifications import executors, models
from apps.notifications.services import (
    NotificationSenderService,
    WhatsAppRateLimiter,
)

logger = logging.getLogger(__name__)


@shared_task(name="notifications.process_campaign_notifications")
def process_campaign_notifications(
    campaign_id: int, campaign_type: str = "GROUP"
) -> dict:
    """
    Schedule notifications for a campaign based on its execution date.

    This task creates a scheduled task in Celery Beat to send notifications
    at the campaign's execution date.

    Args:
        campaign_id: ID of the campaign to process
        campaign_type: Type of campaign ('GROUP' or 'FILE')

    Returns:
        dict: Summary of scheduling result
    """
    logger.info(
        f"Starting to schedule {campaign_type} campaign notifications for campaign {campaign_id}"
    )

    try:
        # Get the appropriate campaign model
        if campaign_type == campaigns_choices.CampaignType.FILE:
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
    except Exception as e:
        logger.error(
            f"{campaign_type.capitalize()} campaign {campaign_id} not found: {e}"
        )
        return {"success": False, "error": "Campaign not found"}

    # Validate execution date
    if not campaign.execution_date:
        logger.error(f"Campaign {campaign_id} has no execution date configured")
        return {"success": False, "error": "No execution date configured"}

    # Create a ClockedSchedule for the campaign's execution date
    clocked, _ = ClockedSchedule.objects.get_or_create(
        clocked_time=campaign.execution_date
    )

    # Create or update the periodic task
    task_name = f"campaign_{campaign_type.lower()}_{campaign_id}_notifications"

    # Remove any existing task with the same name
    PeriodicTask.objects.filter(name=task_name).delete()

    # Create new periodic task
    periodic_task = PeriodicTask.objects.create(
        clocked=clocked,
        name=task_name,
        task="notifications.schedule_campaign_notifications_task",
        args=f'[{campaign_id}, "{campaign_type}"]',
        one_off=True,
        enabled=True,
    )

    # Update campaign status to SCHEDULED
    campaign.update_status(campaigns_choices.CampaignStatus.SCHEDULED)

    logger.info(
        f"Scheduled campaign {campaign_id} notifications to be sent at {campaign.execution_date}"
    )

    return {
        "success": True,
        "message": f"Campaign notifications scheduled for {campaign.execution_date}",
        "scheduled_task_id": periodic_task.id,
        "execution_date": str(campaign.execution_date),
    }


@shared_task(name="notifications.schedule_campaign_notifications_task")
def schedule_campaign_notifications_task(
    campaign_id: int, campaign_type: str = "GROUP"
) -> dict:
    """
    Execute campaign and create notification records.

    This task is scheduled by process_campaign_notifications and runs
    at the campaign's execution date to create notifications.

    Args:
        campaign_id: ID of the campaign to execute
        campaign_type: Type of campaign ('GROUP' or 'FILE')

    Returns:
        dict: Summary of created notifications
    """

    logger.info(
        f"Executing scheduled notifications for {campaign_type} campaign {campaign_id}"
    )

    try:
        # Get the appropriate campaign model
        if campaign_type == campaigns_choices.CampaignType.FILE:
            campaign = campaign_models.CampaignCSVFile.objects.get(
                id=campaign_id
            )
            executor = executors.FileCampaignExecutor(campaign)
        else:
            campaign = campaign_models.Campaign.objects.select_related(
                "group"
            ).get(id=campaign_id)
            executor = executors.GroupCampaignExecutor(campaign)

        # Update campaign status to PROCESSING
        campaign.update_status(campaigns_choices.CampaignStatus.PROCESSING)

        logger.info(
            f"Campaign found: '{campaign.name}' "
            f"(Type: {campaign_type}, Status: {campaign.get_status_display()})"
        )
    except Exception as e:
        logger.error(
            f"{campaign_type.capitalize()} campaign {campaign_id} not found: {e}"
        )
        return {"success": False, "error": "Campaign not found"}

    # Execute the campaign using the executor
    result = executor.execute()

    # Update campaign status to COMPLETED
    campaign.update_status(campaigns_choices.CampaignStatus.COMPLETED)

    logger.info(
        f"Campaign {campaign_id} execution finished - Success: {result.get('success')}. "
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

    # Get all pending notifications scheduled for now or earlier
    pending_notifications = models.CampaignNotification.objects.filter(
        status=campaigns_choices.NotificationStatus.PENDING,
        scheduled_at__lte=timezone.now(),
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
                campaigns_choices.CampaignStatus.ACTIVE,
                campaigns_choices.CampaignStatus.SENDING,
            ]

            if campaign.status not in valid_sending_statuses:
                logger.info(
                    f"Cancelling notification {notification.id} - campaign '{campaign_name}' "
                    f"cannot send notifications (status: {campaign.get_status_display()})"
                )
                notification.status = (
                    campaigns_choices.NotificationStatus.CANCELLED
                )
                notification.save(update_fields=["status"])
                cancelled_count += 1
                continue

            # Transition campaign to SENDING if it's ACTIVE
            if campaign.status == campaigns_choices.CampaignStatus.ACTIVE:
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
    if (
        notification.channel
        == notification_choices.NotificationChannel.WHATSAPP
    ):
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

    # Update campaign status to SENDING
    notification.campaign.update_status(
        campaigns_choices.CampaignStatus.COMPLETED
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
