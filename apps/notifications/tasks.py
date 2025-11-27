import logging

from celery import shared_task
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from apps.campaigns import choices as campaigns_choices
from apps.campaigns import models as campaign_models
from apps.notifications import choices, constants, executors, models, utils
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
    Execute campaign and create notification records, then trigger
    notification sending and finalization.

    This task is scheduled by process_campaign_notifications and runs
    at the campaign's execution date to create notifications.

    Flow:
    1. Update campaign status to PROCESSING
    2. Execute the campaign using the executor (creates notifications)
    3. Update campaign status to SENDING
    4. Trigger send_scheduled_notifications for this campaign
    5. Schedule finalize_campaign_status with calculated countdown

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

    # Execute the campaign using the executor (creates notifications)
    result = executor.execute()

    if not result.get("success"):
        campaign.update_status(campaigns_choices.CampaignStatus.FAILED)
        logger.error(
            f"Campaign {campaign_id} execution failed: {result.get('error', 'Unknown error')}"
        )
        return result

    # Get the number of created notifications
    created_count = result.get("created_count", 0)

    if created_count == 0:
        # No notifications created, mark as completed
        campaign.update_status(campaigns_choices.CampaignStatus.COMPLETED)
        logger.info(
            f"Campaign {campaign_id} completed with no notifications created"
        )
        return result

    # Update campaign status to SENDING
    campaign.update_status(campaigns_choices.CampaignStatus.SENDING)

    logger.info(
        f"Campaign {campaign_id} created {created_count} notifications, "
        f"triggering send process"
    )

    # Trigger notification sending for this campaign
    send_scheduled_notifications.delay(campaign_id, campaign_type)

    # Calculate countdown based on notification count and channel
    countdown = utils.calculate_countdown(created_count, campaign.channel)

    logger.info(
        f"Scheduling finalize_campaign_status for campaign {campaign_id} "
        f"with countdown of {countdown} seconds"
    )

    # Schedule finalization task
    finalize_campaign_status.apply_async(
        args=[campaign_id, campaign_type, 1],
        countdown=countdown,
    )

    logger.info(
        f"Campaign {campaign_id} execution finished - Success: {result.get('success')}. "
        f"Message: {result.get('message', 'N/A')}"
    )

    return result


@shared_task(name="notifications.send_scheduled_notifications")
def send_scheduled_notifications(
    campaign_id: int = None, campaign_type: str = None
) -> dict:
    """
    Send pending notifications for a specific campaign or all campaigns.

    When campaign_id and campaign_type are provided, only notifications
    for that specific campaign are processed. Otherwise, all pending
    notifications scheduled for now or earlier are processed.

    Args:
        campaign_id: Optional campaign ID to filter notifications
        campaign_type: Optional campaign type ('GROUP' or 'FILE')

    Returns:
        dict: Summary of queued notifications
    """
    if campaign_id and campaign_type:
        logger.info(
            f"Starting notifications processing for {campaign_type} "
            f"campaign {campaign_id}"
        )
    else:
        logger.info(
            "Starting scheduled notifications processing (all campaigns)"
        )

    pending_notifications = models.CampaignNotification.objects.filter(
        campaign_id=campaign_id,
    ).select_related("campaign_type", "recipient_type")

    total_pending = pending_notifications.count()
    logger.info(f"Found {total_pending} pending notifications to process")

    if total_pending == 0:
        logger.info("No pending notifications to process")
        return {
            "success": True,
            "queued_count": 0,
            "failed_count": 0,
        }

    queued_count = 0
    failed_count = 0

    for notification in pending_notifications:
        try:
            recipient_name = getattr(
                notification.recipient, "full_name", "Unknown"
            )

            logger.debug(
                f"Queuing notification {notification.id} for recipient '{recipient_name}'"
            )

            # Queue notification for async sending
            send_notification.delay(notification.id)
            queued_count += 1

            logger.info(
                f"Successfully queued notification {notification.id} for sending"
            )

        except Exception as e:
            logger.error(
                f"Failed to queue notification {notification.id}: {e}",
                exc_info=True,
            )
            failed_count += 1

    logger.info(
        f"Notifications processing completed: "
        f"Queued {queued_count}, Failed to queue {failed_count}"
    )

    return {
        "success": True,
        "queued_count": queued_count,
        "failed_count": failed_count,
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
    if notification.channel == choices.NotificationChannel.WHATSAPP:
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


@shared_task(name="notifications.finalize_campaign_status")
def finalize_campaign_status(
    campaign_id: int, campaign_type: str, attempt: int = 1
) -> dict:
    """
    Finalize campaign status after all notifications have been processed.

    This task checks the status of all notifications for a campaign and
    updates the campaign's final status and metrics accordingly.

    If there are still pending notifications and max attempts haven't been
    reached, the task reschedules itself with a new countdown.

    Args:
        campaign_id: ID of the campaign to finalize
        campaign_type: Type of campaign ('GROUP' or 'FILE')
        attempt: Current attempt number (max 10)

    Returns:
        dict: Summary of finalization result
    """
    logger.info(
        f"Finalizing campaign {campaign_id} status - Attempt {attempt}/{constants.MAX_FINALIZE_ATTEMPTS}"
    )

    try:
        campaign = campaign_models.Campaign.objects.get(id=campaign_id)
    except campaign_models.Campaign.DoesNotExist as e:
        logger.error(f"Campaign {campaign_id} not found: {e}")
        return {"success": False, "error": "Campaign not found"}

    # Get notification counts
    notifications = models.CampaignNotification.objects.filter(
        campaign_id=campaign_id,
    )

    total_count = notifications.count()
    sent_count = notifications.filter(
        status=choices.NotificationStatus.SENT
    ).count()
    failed_count = notifications.filter(
        status=choices.NotificationStatus.FAILED
    ).count()
    pending_count = notifications.filter(
        status=choices.NotificationStatus.PENDING
    ).count()

    logger.info(
        f"Campaign {campaign_id} notifications - "
        f"Total: {total_count}, Sent: {sent_count}, "
        f"Failed: {failed_count}, Pending: {pending_count}"
    )

    # If there are pending notifications and we haven't reached max attempts
    if pending_count > 0 and attempt < constants.MAX_FINALIZE_ATTEMPTS:
        countdown = utils.calculate_countdown(pending_count, campaign.channel)

        logger.info(
            f"Campaign {campaign_id} has {pending_count} pending notifications. "
            f"Rescheduling finalization (attempt {attempt + 1}) "
            f"with countdown of {countdown} seconds"
        )

        # Reschedule with incremented attempt
        finalize_campaign_status.apply_async(
            args=[campaign_id, campaign_type, attempt + 1],
            countdown=countdown,
        )

        return {
            "success": True,
            "status": "rescheduled",
            "attempt": attempt,
            "pending_count": pending_count,
            "next_countdown": countdown,
        }

    # Final processing - either all done or max attempts reached
    if pending_count > 0:
        logger.warning(
            f"Campaign {campaign_id} reached max finalization attempts ({constants.MAX_FINALIZE_ATTEMPTS}) "
            f"with {pending_count} notifications still pending. Marking them as CANCELLED."
        )
        # Mark remaining pending notifications as cancelled
        notifications.filter(status=choices.NotificationStatus.PENDING).update(
            status=choices.NotificationStatus.CANCELLED
        )
        cancelled_count = pending_count
    else:
        cancelled_count = 0

    # Update campaign metrics
    campaign.total_sent = sent_count
    campaign.total_failed = failed_count + cancelled_count

    # Determine final status
    if sent_count > 0:
        campaign.status = campaigns_choices.CampaignStatus.COMPLETED
        final_status = "COMPLETED"
    else:
        campaign.status = campaigns_choices.CampaignStatus.FAILED
        final_status = "FAILED"

    campaign.save(update_fields=["status", "total_sent", "total_failed"])

    logger.info(
        f"Campaign {campaign_id} finalized after {attempt} attempts - "
        f"Status: {final_status}, Sent: {sent_count}, "
        f"Failed: {failed_count}, Cancelled: {cancelled_count}"
    )

    return {
        "success": True,
        "status": final_status,
        "attempts": attempt,
        "total_sent": sent_count,
        "total_failed": failed_count,
        "cancelled_count": cancelled_count,
    }
