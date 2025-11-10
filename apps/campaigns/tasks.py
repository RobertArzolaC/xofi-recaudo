import logging

from celery import shared_task

from apps.campaigns import choices, models
from apps.campaigns.services import CSVValidationService

logger = logging.getLogger(__name__)


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


@shared_task(name="campaigns.validate_csv_campaign")
def validate_csv_campaign(campaign_id: int) -> dict:
    """
    Validate CSV/Excel file for a file-based campaign.

    This task parses the uploaded file, validates each contact,
    and creates CSVContact records.

    Args:
        campaign_id: ID of the CampaignCSVFile to validate

    Returns:
        dict: Validation results summary
    """
    logger.info(f"Starting CSV validation for campaign {campaign_id}")

    try:
        campaign_csv = models.CampaignCSVFile.objects.get(id=campaign_id)
    except models.CampaignCSVFile.DoesNotExist:
        logger.error(f"CampaignCSVFile {campaign_id} not found")
        return {"success": False, "error": "Campaign not found"}

    try:
        result = CSVValidationService.validate_campaign_csv(campaign_csv)

        logger.info(
            f"CSV validation completed for campaign {campaign_id}: "
            f"{result['valid_contacts']} valid, {result['invalid_contacts']} invalid"
        )

        return {
            "success": True,
            "campaign_id": campaign_id,
            **result,
        }

    except Exception as e:
        logger.exception(
            f"Error validating CSV for campaign {campaign_id}: {e}"
        )
        return {
            "success": False,
            "campaign_id": campaign_id,
            "error": str(e),
        }
