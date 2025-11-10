"""
Report generators for Collection Groups.

This module contains report generators for group-related reports.
"""

from typing import Any, List

from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from apps.campaigns.models import CampaignNotification, Group
from apps.reports.generators.base import BaseReportGenerator


class CollectionGroupEffectivenessReportGenerator(BaseReportGenerator):
    """
    Generate effectiveness report for collection groups.
    Shows performance metrics by group.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered groups queryset."""
        queryset = Group.objects.prefetch_related(
            "partners", "campaigns", "campaigns__notifications"
        )

        # Apply filters
        priority = self.filters.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        date_from = self.filters.get("date_from")
        date_to = self.filters.get("date_to")

        if date_from or date_to:
            # Filter by campaign creation dates
            campaign_filters = Q()
            if date_from:
                campaign_filters &= Q(campaigns__created__gte=date_from)
            if date_to:
                campaign_filters &= Q(campaigns__created__lte=date_to)
            queryset = queryset.filter(campaign_filters).distinct()

        return queryset.order_by("-priority", "name")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Group Name"),
            _("Priority"),
            _("Total Partners"),
            _("Total Campaigns"),
            _("Active Campaigns"),
            _("Completed Campaigns"),
            _("Total Notifications Sent"),
            _("Successful Notifications"),
            _("Failed Notifications"),
            _("Success Rate %"),
            _("Total Outstanding Debt"),
            _("Overdue Obligations"),
            _("Created Date"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        for group in queryset:
            # Calculate metrics
            partners_count = group.partners.count()
            campaigns = group.campaigns.all()
            total_campaigns = campaigns.count()
            active_campaigns = campaigns.filter(status="active").count()
            completed_campaigns = campaigns.filter(status="completed").count()

            # Notification metrics
            all_notifications = CampaignNotification.objects.filter(
                campaign__group=group
            )
            total_notifications = all_notifications.count()
            sent_notifications = all_notifications.filter(status="sent").count()
            failed_notifications = all_notifications.filter(status="failed").count()

            # Calculate success rate
            success_rate = (
                (sent_notifications / total_notifications * 100)
                if total_notifications > 0
                else 0
            )

            # Debt metrics
            total_debt = group.total_outstanding_debt
            overdue_count = group.overdue_obligations_count

            row = [
                group.name,
                group.get_priority_display(),
                partners_count,
                total_campaigns,
                active_campaigns,
                completed_campaigns,
                total_notifications,
                sent_notifications,
                failed_notifications,
                round(success_rate, 2),
                float(total_debt),
                overdue_count,
                group.created.strftime("%Y-%m-%d %H:%M"),
            ]
            data.append(row)

        return data
