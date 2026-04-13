import logging

from celery import shared_task

from apps.campaigns import models
from apps.campaigns.services import CSVValidationService
from apps.notifications import tasks as notification_tasks

logger = logging.getLogger(__name__)


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

        if result["valid_contacts"] > 0:
            notification_tasks.process_campaign_notifications.delay(
                campaign_id, campaign_csv.campaign_type
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
