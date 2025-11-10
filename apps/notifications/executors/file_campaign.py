import logging
from typing import Dict, Optional

from constance import config

from apps.campaigns import choices as campaign_choices
from apps.notifications import choices
from apps.notifications.executors.base import BaseCampaignExecutor
from apps.notifications.models import CampaignNotification
from apps.payments import choices as payment_choices
from apps.payments import utils as payment_utils

logger = logging.getLogger(__name__)


class FileCampaignExecutor(BaseCampaignExecutor):
    """Executor for file-based (CSV/Excel) campaigns."""

    def can_execute(self) -> bool:
        """
        Check if file campaign can be executed.

        Returns:
            bool: True if campaign can be executed
        """
        return (
            self.campaign.validation_status
            == campaign_choices.ValidationStatus.VALIDATED
            and self.campaign.valid_contacts > 0
            and self.campaign.status
            in [
                campaign_choices.CampaignStatus.ACTIVE,
                campaign_choices.CampaignStatus.SCHEDULED,
            ]
            and not self.campaign.is_processing
            and self.campaign.execution_date is not None
        )

    def validate_campaign(self) -> tuple[bool, Optional[str]]:
        """
        Validate file campaign before execution.

        Returns:
            tuple: (is_valid, error_message)
        """
        if (
            self.campaign.validation_status
            != campaign_choices.ValidationStatus.VALIDATED
        ):
            return (
                False,
                f"CSV file must be validated first (current status: "
                f"{self.campaign.get_validation_status_display()})",
            )

        if self.campaign.valid_contacts == 0:
            return False, "No valid contacts found in CSV file"

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

        return True, None

    def create_notifications(self) -> Dict[str, any]:
        """
        Create notifications for all valid contacts in the CSV.

        Returns:
            dict: Summary of created notifications
        """
        # Get all valid contacts from the CSV
        valid_contacts = self.campaign.csv_contacts.filter(is_valid=True)
        contacts_count = valid_contacts.count()

        self.logger.info(
            f"Processing {contacts_count} valid contacts for campaign {self.campaign.id}"
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        notification_ids = []

        for contact in valid_contacts:
            self.logger.debug(
                f"Processing contact {contact.full_name} (Row: {contact.row_number})"
            )

            # Get recipient identifier for the channel
            recipient_identifier = self.get_recipient_identifier(
                contact, self.campaign.channel
            )

            if not recipient_identifier:
                self.logger.warning(
                    f"Skipping contact {contact.full_name} (Row {contact.row_number}) - "
                    f"no {self.campaign.channel} identifier"
                )
                skipped_count += 1
                continue

            # Generate payment link if configured
            payment_link_url = None
            if self.campaign.use_payment_link:
                payment_link_url = self._generate_payment_link(contact)

            # Create or update notification
            notification, created = self._create_or_update_notification(
                contact=contact,
                recipient_identifier=recipient_identifier,
                payment_link_url=payment_link_url,
            )

            if created:
                created_count += 1
                notification_ids.append(notification.id)
                self.logger.debug(
                    f"Created notification {notification.id} for contact {contact.full_name}"
                )
            else:
                updated_count += 1
                self.logger.debug(
                    f"Updated notification {notification.id} for contact {contact.full_name}"
                )

        result_message = (
            f"Created {created_count} notifications, "
            f"updated {updated_count}, "
            f"skipped {skipped_count} contacts"
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
            "total_contacts": contacts_count,
            "notification_ids": notification_ids,
            "message": result_message,
        }

    def _generate_payment_link(self, contact) -> Optional[str]:
        """
        Generate a payment link for a CSV contact.

        For CSV contacts, we try to find the partner by document number
        or create a generic payment link.

        Args:
            contact: CSVContact instance

        Returns:
            str: Payment link URL or None
        """
        try:
            # Try to find partner by document number
            partner = None
            if contact.document_number:
                from apps.partners.models import Partner

                try:
                    partner = Partner.objects.get(
                        document_number=contact.document_number
                    )
                except Partner.DoesNotExist:
                    self.logger.debug(
                        f"No partner found for document {contact.document_number}"
                    )
                except Partner.MultipleObjectsReturned:
                    self.logger.warning(
                        f"Multiple partners found for document {contact.document_number}"
                    )

            if partner:
                # Generate payment link for existing partner
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
                        f"Generated payment link for contact {contact.full_name}: {payment_link_url}"
                    )
                    return payment_link_url
            else:
                # For CSV contacts without partner, we could create a generic payment link
                # or skip payment link generation
                self.logger.debug(
                    f"Skipping payment link for contact {contact.full_name} - no partner found"
                )
                return None

        except Exception as e:
            self.logger.error(
                f"Failed to generate payment link for contact {contact.full_name}: {e}"
            )
        return None

    def _create_or_update_notification(
        self,
        contact,
        recipient_identifier: str,
        payment_link_url: Optional[str],
    ) -> tuple:
        """
        Create or update a notification for a CSV contact.

        Args:
            contact: CSVContact instance
            recipient_identifier: Recipient contact info
            payment_link_url: Optional payment link URL

        Returns:
            tuple: (notification, created)
        """
        from django.contrib.contenttypes.models import ContentType

        notification_defaults = {
            "recipient_email": contact.email,
            "recipient_phone": contact.phone,
            "recipient_telegram_id": contact.telegram_id,
            "total_debt_amount": contact.amount,
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
        ).get_for_model(self.campaign)
        contact_content_type = ContentType.objects.db_manager(
            "xofi-erp"
        ).get_for_model(contact)

        notification, created = CampaignNotification.objects.update_or_create(
            campaign_type=campaign_content_type,
            campaign_id=self.campaign.id,
            recipient_type=contact_content_type,
            recipient_id=contact.id,
            notification_type=choices.NotificationType.SCHEDULED,
            channel=self.campaign.channel,
            defaults=notification_defaults,
        )

        return notification, created
