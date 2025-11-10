import logging
from typing import Dict

from apps.campaigns import choices
from apps.notifications import executors

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for executing campaigns and creating notifications."""

    @classmethod
    def execute_campaign(cls, campaign) -> Dict[str, any]:
        """
        Execute a campaign and create notifications.

        This method determines the campaign type and delegates to the
        appropriate executor.

        Args:
            campaign: Campaign or CampaignCSVFile instance

        Returns:
            dict: Execution result summary
        """
        # Determine campaign type and get appropriate executor
        executor = cls.get_executor_for_campaign(campaign)

        if not executor:
            return {
                "success": False,
                "error": f"No executor found for campaign type: {campaign.campaign_type}",
            }

        # Execute the campaign
        return executor.execute()

    @classmethod
    def get_executor_for_campaign(cls, campaign):
        """
        Get the appropriate executor for a campaign.

        Args:
            campaign: Campaign or CampaignCSVFile instance

        Returns:
            BaseCampaignExecutor: Appropriate executor instance
        """
        campaign_type = getattr(campaign, "campaign_type", None)

        if campaign_type == choices.CampaignType.GROUP:
            return executors.GroupCampaignExecutor(campaign)
        elif campaign_type == choices.CampaignType.FILE:
            return executors.FileCampaignExecutor(campaign)
        else:
            logger.error(f"Unknown campaign type: {campaign_type}")
            raise ValueError(f"Unknown campaign type: {campaign_type}")

    @classmethod
    def can_execute_campaign(cls, campaign) -> bool:
        """
        Check if a campaign can be executed.

        Args:
            campaign: Campaign or CampaignCSVFile instance

        Returns:
            bool: True if campaign can be executed
        """
        executor = cls.get_executor_for_campaign(campaign)
        if not executor:
            return False
        return executor.can_execute()
