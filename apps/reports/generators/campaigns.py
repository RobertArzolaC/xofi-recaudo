"""
Report generators for Collection Campaigns.

This module contains report generators for campaign-related reports.
"""

from typing import Any, List

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from apps.campaigns.models import Campaign
from apps.notifications import choices as notification_choices
from apps.notifications.models import CampaignNotification
from apps.partners.models import Partner
from apps.reports.generators.base import BaseReportGenerator


class CollectionCampaignsSummaryReportGenerator(BaseReportGenerator):
    """
    Generate summary report of collection campaigns with key metrics.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered campaigns queryset."""
        queryset = Campaign.objects.select_related("group", "created_by")

        # Apply filters
        status = self.filters.get("status")
        if status:
            queryset = queryset.filter(status=status)

        channel = self.filters.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        date_from = self.filters.get("date_from")
        if date_from:
            queryset = queryset.filter(created__gte=date_from)

        date_to = self.filters.get("date_to")
        if date_to:
            queryset = queryset.filter(created__lte=date_to)

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Campaign Name"),
            _("Status"),
            _("Channel"),
            _("Group"),
            _("Target Amount"),
            _("Average Cost"),
            _("Total Notifications"),
            _("Sent Notifications"),
            _("Failed Notifications"),
            _("Execution Count"),
            _("Last Execution"),
            _("Created By"),
            _("Created Date"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        # Get ContentType for Campaign model
        campaign_content_type = ContentType.objects.get_for_model(Campaign)

        for campaign in queryset:
            # Get notification summary using GenericForeignKey
            notifications = CampaignNotification.objects.filter(
                campaign_type=campaign_content_type, campaign_id=campaign.id
            )
            total_notifications = notifications.count()
            sent_count = notifications.filter(
                status=notification_choices.NotificationStatus.SENT
            ).count()
            failed_count = notifications.filter(
                status=notification_choices.NotificationStatus.FAILED
            ).count()

            row = [
                campaign.name,
                campaign.get_status_display(),
                campaign.get_channel_display(),
                campaign.group.name if campaign.group else "-",
                float(campaign.target_amount) if campaign.target_amount else 0,
                float(campaign.average_cost) if campaign.average_cost else 0,
                total_notifications,
                sent_count,
                failed_count,
                campaign.execution_count,
                campaign.last_execution_at.strftime("%Y-%m-%d %H:%M")
                if campaign.last_execution_at
                else "-",
                campaign.created_by.full_name if campaign.created_by else "-",
                campaign.created.strftime("%Y-%m-%d %H:%M"),
            ]
            data.append(row)

        return data


class CampaignNotificationsDetailReportGenerator(BaseReportGenerator):
    """
    Generate detailed report of campaign notifications.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered notifications queryset."""
        # CampaignNotification uses GenericForeignKey for campaign and recipient
        # We can't use select_related on GenericFK, need to handle differently
        queryset = CampaignNotification.objects.select_related(
            "campaign_type", "recipient_type", "created_by"
        )

        # Apply filters
        campaign_id = self.filters.get("campaign_id")
        if campaign_id:
            # Need to also filter by campaign_type for proper GenericFK filtering
            campaign_content_type = ContentType.objects.get_for_model(Campaign)
            queryset = queryset.filter(
                campaign_type=campaign_content_type, campaign_id=campaign_id
            )

        status = self.filters.get("status")
        if status:
            queryset = queryset.filter(status=status)

        channel = self.filters.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        notification_type = self.filters.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        date_from = self.filters.get("date_from")
        if date_from:
            queryset = queryset.filter(created__gte=date_from)

        date_to = self.filters.get("date_to")
        if date_to:
            queryset = queryset.filter(created__lte=date_to)

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Campaign"),
            _("Recipient Document"),
            _("Recipient Name"),
            _("Notification Type"),
            _("Channel"),
            _("Status"),
            _("Recipient Email"),
            _("Recipient Phone"),
            _("Total Debt Amount"),
            _("Included Payment Link"),
            _("Payment Link URL"),
            _("Scheduled At"),
            _("Sent At"),
            _("Error Message"),
            _("Created Date"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        # Cache for campaign and recipient lookups to avoid N+1 queries
        campaign_cache = {}
        recipient_cache = {}

        for notification in queryset:
            # Get campaign name via GenericFK
            campaign_key = (notification.campaign_type_id, notification.campaign_id)
            if campaign_key not in campaign_cache:
                try:
                    campaign_obj = notification.campaign
                    campaign_cache[campaign_key] = (
                        campaign_obj.name if campaign_obj else "-"
                    )
                except Exception:
                    campaign_cache[campaign_key] = "-"

            # Get recipient info via GenericFK
            recipient_key = (notification.recipient_type_id, notification.recipient_id)
            if recipient_key not in recipient_cache:
                try:
                    recipient_obj = notification.recipient
                    if recipient_obj:
                        # Check if it's a Partner or CSVContact
                        doc_number = getattr(
                            recipient_obj, "document_number", "-"
                        ) or getattr(recipient_obj, "phone", "-")
                        full_name = getattr(recipient_obj, "full_name", "-")
                        recipient_cache[recipient_key] = (doc_number, full_name)
                    else:
                        recipient_cache[recipient_key] = ("-", "-")
                except Exception:
                    recipient_cache[recipient_key] = ("-", "-")

            campaign_name = campaign_cache[campaign_key]
            recipient_doc, recipient_name = recipient_cache[recipient_key]

            row = [
                campaign_name,
                recipient_doc,
                recipient_name,
                notification.get_notification_type_display(),
                notification.get_channel_display(),
                notification.get_status_display(),
                notification.recipient_email or "-",
                notification.recipient_phone or "-",
                float(notification.total_debt_amount)
                if notification.total_debt_amount
                else 0,
                "Yes" if notification.included_payment_link else "No",
                notification.payment_link_url or "-",
                notification.scheduled_at.strftime("%Y-%m-%d %H:%M")
                if notification.scheduled_at
                else "-",
                notification.sent_at.strftime("%Y-%m-%d %H:%M")
                if notification.sent_at
                else "-",
                notification.error_message or "-",
                notification.created.strftime("%Y-%m-%d %H:%M"),
            ]
            data.append(row)

        return data
