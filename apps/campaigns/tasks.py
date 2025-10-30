import logging

from celery import shared_task
from django.utils import timezone

from apps.campaigns import choices, models
from apps.campaigns.utils import messages as message_utils
from apps.core.services.chats.telegram import telegram_service
from apps.core.services.chats.whatsapp import whatsapp_service
from apps.partners import services as partner_services
from apps.payments.utils import generate_payment_link_for_debt

logger = logging.getLogger(__name__)


@shared_task(
    name="campaigns.send_whatsapp_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_notification(self, notification_id: int) -> dict:
    """
    Send a notification for a campaign.

    Args:
        notification_id: ID of the CampaignNotification to send

    Returns:
        dict: Result with success status and details
    """
    try:
        notification = models.CampaignNotification.objects.select_related(
            "campaign", "partner"
        ).get(id=notification_id)
    except models.CampaignNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {"success": False, "error": "Notification not found"}

    # Increment attempt counter
    notification.increment_attempt()

    # Determine which service to use based on notification channel
    if notification.channel == choices.NotificationChannel.TELEGRAM:
        messaging_service = telegram_service
        channel_name = "Telegram"
    elif notification.channel == choices.NotificationChannel.WHATSAPP:
        messaging_service = whatsapp_service
        channel_name = "WhatsApp"
    else:
        error_msg = f"Unsupported notification channel: {notification.channel}"
        logger.error(error_msg)
        notification.mark_as_failed(error_msg)
        return {"success": False, "error": error_msg}

    # Check if service is configured
    if not messaging_service.is_configured():
        error_msg = f"{channel_name} service is not configured"
        logger.error(error_msg)
        notification.mark_as_failed(error_msg)
        return {"success": False, "error": error_msg}

    # Get message template
    try:
        template = models.MessageTemplate.objects.get(
            template_type=notification.notification_type,
            channel=notification.channel,
            is_active=True,
        )
    except models.MessageTemplate.DoesNotExist:
        error_msg = (
            f"No active template found for "
            f"{notification.get_notification_type_display()} on {channel_name}"
        )
        logger.warning(error_msg)
        # Use default message if no template exists
        template = None

    # Get detailed debt information for the partner
    debt_detail = (
        partner_services.PartnerDebtService.get_single_partner_debt_detail(
            notification.partner
        )
    )

    # Prepare message context
    context = message_utils.prepare_message_context(notification, debt_detail)

    # Render message
    if template:
        message = template.render_message(context)
        include_payment_button = template.include_payment_button
        payment_button_text = template.payment_button_text
    else:
        message = message_utils.generate_default_message(
            notification, context, debt_detail
        )
        include_payment_button = notification.included_payment_link
        payment_button_text = "Pagar ahora"

    # Store the rendered message
    notification.message_content = message
    notification.save(update_fields=["message_content"])

    # Send message via the appropriate service
    try:
        # Prepare recipient identifier based on channel
        if notification.channel == choices.NotificationChannel.WHATSAPP:
            recipient_identifier = notification.recipient_phone
        elif notification.channel == choices.NotificationChannel.TELEGRAM:
            recipient_identifier = notification.recipient_phone
        else:
            recipient_identifier = notification.recipient_phone

        if include_payment_button and notification.payment_link_url:
            # Send message with payment link button
            # Both services use the same method signature
            if notification.channel == choices.NotificationChannel.WHATSAPP:
                result = messaging_service.send_message_with_button(
                    recipient_phone=recipient_identifier,
                    message=message,
                    button_text=payment_button_text,
                    button_url=notification.payment_link_url,
                )
            elif notification.channel == choices.NotificationChannel.TELEGRAM:
                result = messaging_service.send_message_with_button(
                    recipient_id=recipient_identifier,
                    message=message,
                    button_text=payment_button_text,
                    button_url=notification.payment_link_url,
                )
        else:
            # Send plain text message
            if notification.channel == choices.NotificationChannel.WHATSAPP:
                result = messaging_service.send_text_message(
                    recipient_phone=recipient_identifier,
                    message=message,
                )
            elif notification.channel == choices.NotificationChannel.TELEGRAM:
                result = messaging_service.send_text_message(
                    recipient_id=recipient_identifier,
                    message=message,
                )

        if result.get("success"):
            notification.mark_as_sent()
            logger.info(
                f"Notification {notification_id} sent successfully "
                f"to {notification.partner.full_name} ({notification.recipient_phone})"
            )
            return {
                "success": True,
                "notification_id": notification_id,
                "response": result.get("response"),
            }
        else:
            error_msg = result.get("error", "Unknown error")
            notification.mark_as_failed(error_msg)
            logger.error(
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


@shared_task(name="campaigns.process_campaign_notifications")
def process_campaign_notifications(campaign_id: int) -> dict:
    """
    Process and schedule notifications for a campaign.

    This task creates notification records for all partners in the campaign
    based on their debts and the campaign's execution date.

    Args:
        campaign_id: ID of the campaign to process

    Returns:
        dict: Summary of created notifications
    """
    logger.info(
        f"Starting to process campaign notifications for campaign {campaign_id}"
    )

    try:
        campaign = models.Campaign.objects.select_related("group").get(
            id=campaign_id
        )
        logger.info(
            f"Campaign found: '{campaign.name}' (Status: {campaign.get_status_display()})"
        )
    except models.Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {"success": False, "error": "Campaign not found"}

    # Check if campaign can be executed
    logger.info(f"Validating campaign {campaign_id} execution requirements")
    if not campaign.can_be_executed:
        reasons = []
        valid_statuses = [
            choices.CampaignStatus.ACTIVE,
            choices.CampaignStatus.SCHEDULED,
        ]
        if campaign.status not in valid_statuses:
            reasons.append(
                f"Campaign status is {campaign.get_status_display()}, must be ACTIVE or SCHEDULED"
            )
        if campaign.is_processing:
            reasons.append("Campaign is already being processed")
        if not campaign.execution_date:
            reasons.append("Campaign has no execution date")
        if not campaign.group:
            reasons.append("Campaign has no group assigned")

        error_msg = "; ".join(reasons)
        logger.warning(
            f"Campaign {campaign_id} cannot be executed: {error_msg}"
        )
        return {"success": False, "error": error_msg}

    logger.info(
        f"Campaign {campaign_id} validation passed - ready for execution"
    )

    # Try to acquire execution lock
    logger.info(
        f"Attempting to acquire execution lock for campaign {campaign_id}"
    )
    if not campaign.start_execution():
        logger.warning(
            f"Campaign {campaign_id} is already being processed by another worker"
        )
        return {
            "success": False,
            "error": "Campaign is already being processed",
        }

    logger.info(
        f"Execution lock acquired for campaign {campaign_id}. "
        f"Status changed to: {campaign.get_status_display()}"
    )

    # Get all partners in the campaign group
    partners = campaign.group.partners.all()
    partners_count = partners.count()
    logger.info(
        f"Found {partners_count} partners in group '{campaign.group.name}' for campaign {campaign_id}"
    )

    created_count = 0
    skipped_count = 0
    notification_ids = []
    success = False
    result_message = None

    try:
        logger.info(
            f"Starting to process {partners_count} partners for campaign {campaign_id}"
        )

        for partner in partners:
            logger.info(
                f"Processing partner '{partner.full_name}' (ID: {partner.id}) for campaign {campaign_id}"
            )

            # Get partner's debt information
            partner_debt = partner_services.PartnerDebtService.get_single_partner_debt_detail(
                partner
            )

            # Skip partners with no debt
            if partner_debt["total_debt"] == 0:
                logger.info(
                    f"Skipping partner '{partner.full_name}' - no debt (${partner_debt['total_debt']})"
                )
                skipped_count += 1
                continue

            logger.info(
                f"Partner '{partner.full_name}' has debt of ${partner_debt['total_debt']}"
            )

            # Generate payment link if configured
            payment_link_url = None
            if campaign.use_payment_link:
                logger.info(
                    f"Generating payment link for partner '{partner.full_name}'"
                )
                payment_link_url = generate_payment_link_for_debt(
                    partner_id=partner.id,
                    debt_amount=partner_debt["total_debt"],
                    campaign_id=campaign.id,
                )

            # Create or update notification
            notification, created = (
                models.CampaignNotification.objects.update_or_create(
                    campaign=campaign,
                    partner=partner,
                    notification_type=choices.NotificationType.SCHEDULED,
                    channel=choices.NotificationChannel.TELEGRAM,
                    defaults={
                        "recipient_email": partner.email,
                        "recipient_phone": partner.phone,
                        "total_debt_amount": partner_debt["total_debt"],
                        "included_payment_link": campaign.use_payment_link,
                        "payment_link_url": payment_link_url,
                        "scheduled_at": campaign.execution_date,
                        "status": choices.NotificationStatus.PENDING,
                        "created_by": campaign.created_by,
                        "modified_by": campaign.modified_by,
                    },
                )
            )

            if created:
                created_count += 1
                notification_ids.append(notification.id)
                logger.info(
                    f"Created new notification for partner '{partner.full_name}' (Notification ID: {notification.id})"
                )
            else:
                logger.info(
                    f"Updated existing notification for partner '{partner.full_name}' (Notification ID: {notification.id})"
                )

        success = True
        result_message = f"Created {created_count} notifications, skipped {skipped_count} partners (no debt)"
        logger.info(
            f"Campaign {campaign_id} processing completed: "
            f"Created {created_count} notifications, "
            f"Skipped {skipped_count} partners (no debt), "
            f"Total partners processed: {partners_count}"
        )

    except Exception as e:
        success = False
        result_message = f"Error processing campaign: {str(e)}"
        logger.exception(f"Error processing campaign {campaign_id}: {str(e)}")

    finally:
        # Always release the execution lock
        logger.info(f"Releasing execution lock for campaign {campaign_id}")
        campaign.finish_execution(
            success=success, result_message=result_message
        )
        # Refresh from database to get updated status
        campaign.refresh_from_db()
        logger.info(
            f"Campaign {campaign_id} processing finished - Success: {success}. "
            f"Final status: {campaign.get_status_display()}"
        )

    return {
        "success": success,
        "campaign_id": campaign_id,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "total_partners": partners_count,
        "notification_ids": notification_ids,
        "message": result_message,
    }


@shared_task(name="campaigns.update_campaign_status")
def update_campaign_status() -> dict:
    """
    Update campaign status based on notification completion.

    This task checks ACTIVE and SENDING campaigns to see if they should be marked
    as COMPLETED when all their notifications have been processed.

    Flow transitions:
    - ACTIVE → COMPLETED (if all notifications processed and some sent)
    - SENDING → COMPLETED (if all notifications processed and some sent)

    Returns:
        dict: Summary of updated campaigns
    """
    logger.info("Starting campaign status update process")

    # Get campaigns that might need status update
    campaigns_to_check = models.Campaign.objects.filter(
        status__in=[
            choices.CampaignStatus.ACTIVE,
            choices.CampaignStatus.SENDING,
        ],
        is_processing=False,  # Don't update campaigns currently being processed
    )

    updated_count = 0
    status_transitions = []

    for campaign in campaigns_to_check:
        if campaign.should_be_completed():
            old_status = campaign.get_status_display()
            campaign.status = choices.CampaignStatus.COMPLETED
            campaign.save(update_fields=["status"])
            updated_count += 1

            summary = campaign.get_notification_summary()
            transition = f"{old_status} → COMPLETED"
            status_transitions.append(transition)

            logger.info(
                f"Campaign {campaign.id} '{campaign.name}' status updated: {transition}. "
                f"Stats: {summary['sent_notifications']} sent, "
                f"{summary['failed_notifications']} failed, "
                f"{summary['cancelled_notifications']} cancelled"
            )

    logger.info(
        f"Campaign status update completed. Updated {updated_count} campaigns."
    )

    if status_transitions:
        logger.info(f"Status transitions: {', '.join(status_transitions)}")

    return {
        "success": True,
        "updated_count": updated_count,
        "transitions": status_transitions,
    }


@shared_task(name="campaigns.send_scheduled_notifications")
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
        status=choices.NotificationStatus.PENDING,
        scheduled_at__lte=now,
    ).select_related("campaign", "partner")

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
        logger.info(
            f"Processing notification {notification.id} for partner '{notification.partner.full_name}' "
            f"from campaign '{notification.campaign.name}'"
        )

        campaign = notification.campaign

        # Check if campaign can send notifications
        valid_sending_statuses = [
            choices.CampaignStatus.ACTIVE,
            choices.CampaignStatus.SENDING,
        ]

        if campaign.status not in valid_sending_statuses:
            logger.info(
                f"Cancelling notification {notification.id} - campaign '{campaign.name}' "
                f"cannot send notifications (status: {campaign.get_status_display()})"
            )
            notification.status = choices.NotificationStatus.CANCELLED
            notification.save(update_fields=["status"])
            cancelled_count += 1
            continue

        # Transition campaign to SENDING if it's ACTIVE
        if campaign.status == choices.CampaignStatus.ACTIVE:
            campaigns_to_update.add(campaign.id)

        # Send notification asynchronously
        try:
            send_notification.delay(notification.id)
            sent_count += 1
            logger.info(
                f"Successfully queued notification {notification.id} for sending"
            )
        except Exception as e:
            logger.error(f"Failed to queue notification {notification.id}: {e}")
            failed_count += 1

    # Update campaign statuses to SENDING
    if campaigns_to_update:
        updated = models.Campaign.objects.filter(
            id__in=campaigns_to_update,
            status=choices.CampaignStatus.ACTIVE,
        ).update(status=choices.CampaignStatus.SENDING)

        logger.info(
            f"Transitioned {updated} campaigns from ACTIVE to SENDING status"
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
