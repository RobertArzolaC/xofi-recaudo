import logging
from decimal import Decimal
from typing import Dict, Optional

from constance import config
from django.contrib.contenttypes.models import ContentType

from apps.campaigns import choices as campaign_choices
from apps.campaigns import models as campaign_models
from apps.notifications import choices
from apps.notifications.executors.base import BaseCampaignExecutor
from apps.notifications.models import CampaignNotification
from apps.partners import models as partner_models
from apps.partners import services as partner_services
from apps.payments import choices as payment_choices
from apps.payments import utils as payment_utils

logger = logging.getLogger(__name__)


class GroupCampaignExecutor(BaseCampaignExecutor):
    """Executor for group-based campaigns."""

    def can_execute(self) -> bool:
        """
        Check if group campaign can be executed.

        Returns:
            bool: True if campaign can be executed
        """
        valid_statuses = [
            campaign_choices.CampaignStatus.ACTIVE,
            campaign_choices.CampaignStatus.SCHEDULED,
        ]
        return (
            self.campaign.status in valid_statuses
            and not self.campaign.is_processing
            and self.campaign.execution_date is not None
            and self.campaign.group is not None
        )

    def validate_campaign(self) -> tuple[bool, Optional[str]]:
        """
        Validate group campaign before execution.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.campaign.group:
            return False, "Campaign has no group assigned"

        if not self.campaign.execution_date:
            return False, "Campaign has no execution date"

        valid_statuses = [
            campaign_choices.CampaignStatus.ACTIVE,
            campaign_choices.CampaignStatus.SCHEDULED,
        ]
        if self.campaign.status not in valid_statuses:
            return (
                False,
                f"Campaign status is {self.campaign.get_status_display()}, "
                f"must be ACTIVE or SCHEDULED",
            )

        if self.campaign.is_processing:
            return False, "Campaign is already being processed"

        # Check if group has partners
        partners_count = self.campaign.group.partners.count()
        if partners_count == 0:
            return False, "Group has no partners"

        return True, None

    def create_notifications(self) -> Dict[str, any]:
        """
        Create notifications for all partners in the group.

        Returns:
            dict: Summary of created notifications
        """
        partners = self.campaign.group.partners.all()
        partners_count = partners.count()

        self.logger.info(
            f"Processing {partners_count} partners for campaign {self.campaign.id}"
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        notification_ids = []

        for partner in partners:
            self.logger.debug(
                f"Processing partner {partner.full_name} (ID: {partner.id})"
            )

            # Get partner's debt information
            partner_debt = partner_services.PartnerDebtService.get_single_partner_debt_detail(
                partner
            )

            # Skip partners with no debt
            if not self.should_create_notification(
                partner, debt_amount=partner_debt["total_debt"]
            ):
                skipped_count += 1
                continue

            self.logger.debug(
                f"Partner {partner.full_name} has debt of ${partner_debt['total_debt']}"
            )

            # Generate payment link if configured
            payment_link_url = None
            if self.campaign.use_payment_link:
                payment_link_url = self._generate_payment_link(partner)

            # Get recipient identifier for the channel
            recipient_identifier = self.get_recipient_identifier(
                partner, self.campaign.channel
            )

            if not recipient_identifier:
                self.logger.warning(
                    f"Skipping partner {partner.full_name} - no {self.campaign.channel} identifier"
                )
                skipped_count += 1
                continue

            # Create or update notification
            notification, created = self._create_or_update_notification(
                partner=partner,
                recipient_identifier=recipient_identifier,
                debt_amount=partner_debt["total_debt"],
                payment_link_url=payment_link_url,
            )

            if created:
                created_count += 1
                notification_ids.append(notification.id)
                self.logger.debug(
                    f"Created notification {notification.id} for partner {partner.full_name}"
                )
            else:
                updated_count += 1
                self.logger.debug(
                    f"Updated notification {notification.id} for partner {partner.full_name}"
                )

        result_message = (
            f"Created {created_count} notifications, "
            f"updated {updated_count}, "
            f"skipped {skipped_count} partners"
        )

        self.logger.info(
            f"Campaign {self.campaign.id} processing completed: {result_message}"
        )

        return {
            "success": True,
            "campaign_id": self.campaign.id,
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "total_partners": partners_count,
            "notification_ids": notification_ids,
            "message": result_message,
        }

    def _generate_payment_link(self, partner) -> Optional[str]:
        """
        Generate a payment link for a partner.

        Args:
            partner: Partner instance

        Returns:
            str: Payment link URL or None
        """
        try:
            magic_link = payment_utils.create_magic_link_for_partner(
                partner=partner,
                hours_to_expire=24,
                include_upcoming=True,
                source=payment_choices.MagicLinkSource.AUTOMATED,
            )
            if magic_link:
                payment_link_path = magic_link.get_public_url()
                payment_link_url = (
                    f"http://{config.COMPANY_DOMAIN}{payment_link_path}"
                )
                self.logger.debug(
                    f"Generated payment link for partner {partner.full_name}: {payment_link_url}"
                )
                return payment_link_url
        except Exception as e:
            self.logger.error(
                f"Failed to generate payment link for partner {partner.full_name}: {e}"
            )
        return None

    def _create_or_update_notification(
        self,
        partner,
        recipient_identifier: str,
        debt_amount: Decimal,
        payment_link_url: Optional[str],
    ) -> tuple:
        """
        Create or update a notification for a partner.

        Args:
            partner: Partner instance
            recipient_identifier: Recipient contact info
            debt_amount: Total debt amount
            payment_link_url: Optional payment link URL

        Returns:
            tuple: (notification, created)
        """

        notification_defaults = {
            "recipient_email": partner.email,
            "recipient_phone": partner.phone,
            "recipient_telegram_id": partner.telegram_id,
            "total_debt_amount": debt_amount,
            "included_payment_link": self.campaign.use_payment_link,
            "payment_link_url": payment_link_url,
            "scheduled_at": self.campaign.execution_date,
            "status": choices.NotificationStatus.PENDING,
            "created_by": self.campaign.created_by,
            "modified_by": self.campaign.modified_by,
        }

        # Get content types dynamically based on actual instance types
        # Use the xofi-erp database explicitly since that's where notifications are stored
        campaign_content_type = ContentType.objects.db_manager(
            "xofi-erp"
        ).get_for_model(campaign_models.Campaign)
        partner_content_type = ContentType.objects.db_manager(
            "xofi-erp"
        ).get_for_model(partner_models.Partner)

        notification, created = CampaignNotification.objects.update_or_create(
            campaign_type=campaign_content_type,
            campaign_id=self.campaign.id,
            recipient_type=partner_content_type,
            recipient_id=partner.id,
            notification_type=choices.NotificationType.SCHEDULED,
            channel=self.campaign.channel,
            defaults=notification_defaults,
        )

        return notification, created
