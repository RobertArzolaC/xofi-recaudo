"""
Base campaign executor.

This module defines the abstract base class for all campaign executors.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from apps.campaigns import choices

logger = logging.getLogger(__name__)


class BaseCampaignExecutor(ABC):
    """
    Abstract base class for campaign executors.

    Campaign executors handle the business logic for creating and managing
    notifications for different types of campaigns.
    """

    def __init__(self, campaign):
        """
        Initialize the executor with a campaign instance.

        Args:
            campaign: Campaign or CampaignCSVFile instance
        """
        self.campaign = campaign
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def can_execute(self) -> bool:
        """
        Check if the campaign can be executed.

        Returns:
            bool: True if campaign can be executed
        """
        pass

    @abstractmethod
    def validate_campaign(self) -> tuple[bool, Optional[str]]:
        """
        Validate campaign before execution.

        Returns:
            tuple: (is_valid, error_message)
        """
        pass

    @abstractmethod
    def create_notifications(self) -> Dict[str, any]:
        """
        Create notifications for the campaign.

        Returns:
            dict: Summary of created notifications
        """
        pass

    def start_execution(self) -> bool:
        """
        Mark campaign as being processed.

        Returns:
            bool: True if execution lock was acquired
        """
        return self.campaign.start_execution()

    def finish_execution(
        self, success: bool = True, result_message: Optional[str] = None
    ):
        """
        Mark campaign execution as finished.

        Args:
            success: Whether execution was successful
            result_message: Optional result message
        """
        self.campaign.finish_execution(success, result_message)

    def execute(self) -> Dict[str, any]:
        """
        Execute the campaign (main entry point).

        Returns:
            dict: Execution result summary
        """
        self.logger.info(
            f"Starting execution for campaign {self.campaign.id} - {self.campaign.name}"
        )

        # Validate campaign
        is_valid, error_message = self.validate_campaign()
        if not is_valid:
            self.logger.warning(
                f"Campaign {self.campaign.id} validation failed: {error_message}"
            )
            return {"success": False, "error": error_message}

        # Acquire execution lock
        if not self.start_execution():
            error_msg = "Campaign is already being processed"
            self.logger.warning(f"Campaign {self.campaign.id} - {error_msg}")
            return {"success": False, "error": error_msg}

        try:
            # Create notifications
            result = self.create_notifications()

            # Finish execution successfully
            self.finish_execution(
                success=True,
                result_message=result.get("message", "Execution completed"),
            )

            self.logger.info(
                f"Campaign {self.campaign.id} execution completed successfully"
            )
            return result

        except Exception as e:
            error_msg = f"Error during execution: {str(e)}"
            self.logger.exception(
                f"Campaign {self.campaign.id} execution failed: {error_msg}"
            )

            # Finish execution with failure
            self.finish_execution(success=False, result_message=error_msg)

            return {"success": False, "error": error_msg}

    def get_recipient_identifier(
        self, recipient, channel: str
    ) -> Optional[str]:
        """
        Get the appropriate recipient identifier for a channel.

        Args:
            recipient: Recipient object (Partner or CSVContact)
            channel: Notification channel

        Returns:
            str: Recipient identifier (phone, email, etc.)
        """
        if channel == choices.NotificationChannel.WHATSAPP:
            return getattr(recipient, "phone", None)
        elif channel == choices.NotificationChannel.TELEGRAM:
            # For telegram, we might need a specific field or use phone
            return getattr(recipient, "telegram_id", None) or getattr(
                recipient, "phone", None
            )
        elif channel == choices.NotificationChannel.EMAIL:
            return getattr(recipient, "email", None)
        elif channel == choices.NotificationChannel.SMS:
            return getattr(recipient, "phone", None)
        return None

    def should_create_notification(self, recipient, debt_amount=None) -> bool:
        """
        Determine if a notification should be created for a recipient.

        Args:
            recipient: Recipient object
            debt_amount: Optional debt amount

        Returns:
            bool: True if notification should be created
        """
        # Default implementation: create notification if debt > 0
        if debt_amount is not None and debt_amount <= 0:
            self.logger.debug(
                f"Skipping notification for {recipient} - no debt"
            )
            return False
        return True
