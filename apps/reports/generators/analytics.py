"""
Report generators for Analytics and KPIs.

This module contains report generators for KPIs and audit reports.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List

from django.db.models import QuerySet, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.campaigns.models import Campaign
from apps.credits.models import Installment
from apps.notifications.models import CampaignNotification
from apps.payments.models import MagicPaymentLink, Payment
from apps.reports.generators.base import BaseReportGenerator


class CollectionMonthlyKPIsReportGenerator(BaseReportGenerator):
    """
    Generate monthly KPIs report for collection activities.
    Aggregates key metrics by month.
    """

    def get_queryset(self) -> QuerySet:
        """Get date range for monthly aggregation."""
        # This generator works differently - we'll create synthetic data per month
        # Return empty queryset as we'll process in get_data
        return Campaign.objects.none()

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Year"),
            _("Month"),
            _("Total Campaigns"),
            _("Active Campaigns"),
            _("Completed Campaigns"),
            _("Total Notifications Sent"),
            _("Successful Notifications"),
            _("Notification Success Rate %"),
            _("Total Amount Collected"),
            _("Total Payments"),
            _("Average Payment Amount"),
            _("Magic Links Created"),
            _("Magic Links Used"),
            _("Link Conversion Rate %"),
            _("Overdue Installments"),
            _("Total Overdue Amount"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform data into monthly KPI report."""
        data = []

        # Get date range from filters
        date_from = self.filters.get("date_from")
        date_to = self.filters.get("date_to")

        if not date_from or not date_to:
            # Default to last 12 months
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=365)
        else:
            # Convert to date if datetime
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

        # Generate monthly periods
        current_date = date_from.replace(day=1)
        end_date = date_to.replace(day=1)

        while current_date <= end_date:
            # Calculate next month
            if current_date.month == 12:
                next_month = current_date.replace(
                    year=current_date.year + 1, month=1
                )
            else:
                next_month = current_date.replace(month=current_date.month + 1)

            # Campaign metrics
            campaigns = Campaign.objects.filter(
                created__gte=current_date, created__lt=next_month
            )
            total_campaigns = campaigns.count()
            active_campaigns = campaigns.filter(status="active").count()
            completed_campaigns = campaigns.filter(status="completed").count()

            # Notification metrics
            notifications = CampaignNotification.objects.filter(
                created__gte=current_date, created__lt=next_month
            )
            total_notifications = notifications.count()
            successful_notifications = notifications.filter(
                status="sent"
            ).count()
            notification_success_rate = (
                (successful_notifications / total_notifications * 100)
                if total_notifications > 0
                else 0
            )

            # Payment metrics
            payments = Payment.objects.filter(
                payment_date__gte=current_date,
                payment_date__lt=next_month,
                status="paid",
            )
            total_amount = payments.aggregate(Sum("amount"))[
                "amount__sum"
            ] or Decimal("0")
            total_payments = payments.count()
            avg_payment = (
                total_amount / total_payments
                if total_payments > 0
                else Decimal("0")
            )

            # Magic link metrics
            links = MagicPaymentLink.objects.filter(
                created__gte=current_date, created__lt=next_month
            )
            links_created = links.count()
            links_used = links.filter(status="used").count()
            link_conversion = (
                (links_used / links_created * 100) if links_created > 0 else 0
            )

            # Overdue metrics (as of end of month)
            overdue_installments = Installment.objects.filter(
                status__in=["pending", "partial"], due_date__lt=next_month
            )
            overdue_count = overdue_installments.count()
            overdue_amount = overdue_installments.aggregate(
                Sum("installment_amount")
            )["installment_amount__sum"] or Decimal("0")

            row = [
                current_date.year,
                current_date.strftime("%B"),
                total_campaigns,
                active_campaigns,
                completed_campaigns,
                total_notifications,
                successful_notifications,
                round(notification_success_rate, 2),
                float(total_amount),
                total_payments,
                float(avg_payment),
                links_created,
                links_used,
                round(link_conversion, 2),
                overdue_count,
                float(overdue_amount),
            ]
            data.append(row)

            current_date = next_month

        return data


class CollectionManagementAuditReportGenerator(BaseReportGenerator):
    """
    Generate comprehensive audit report for collection management.
    Shows all collection activities with user tracking.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered campaigns for audit trail."""
        queryset = Campaign.objects.select_related(
            "group", "created_by", "modified_by"
        ).prefetch_related("notifications")

        # Apply filters
        date_from = self.filters.get("date_from")
        if date_from:
            queryset = queryset.filter(created__gte=date_from)

        date_to = self.filters.get("date_to")
        if date_to:
            queryset = queryset.filter(created__lte=date_to)

        status = self.filters.get("status")
        if status:
            queryset = queryset.filter(status=status)

        created_by_id = self.filters.get("created_by_id")
        if created_by_id:
            queryset = queryset.filter(created_by_id=created_by_id)

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Campaign Name"),
            _("Status"),
            _("Channel"),
            _("Group"),
            _("Target Amount"),
            _("Execution Count"),
            _("Total Notifications"),
            _("Sent"),
            _("Failed"),
            _("Success Rate %"),
            _("Created By"),
            _("Modified By"),
            _("Created Date"),
            _("Modified Date"),
            _("Last Execution"),
            _("Execution Result"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into audit report data."""
        data = []

        for campaign in queryset:
            # Calculate notification metrics
            notifications = campaign.notifications.all()
            total_notifications = notifications.count()
            sent_count = notifications.filter(status="sent").count()
            failed_count = notifications.filter(status="failed").count()
            success_rate = (
                (sent_count / total_notifications * 100)
                if total_notifications > 0
                else 0
            )

            row = [
                campaign.name,
                campaign.get_status_display(),
                campaign.get_channel_display(),
                campaign.group.name if campaign.group else "-",
                float(campaign.target_amount) if campaign.target_amount else 0,
                campaign.execution_count,
                total_notifications,
                sent_count,
                failed_count,
                round(success_rate, 2),
                campaign.created_by.full_name if campaign.created_by else "-",
                campaign.modified_by.full_name if campaign.modified_by else "-",
                campaign.created.strftime("%Y-%m-%d %H:%M"),
                campaign.modified.strftime("%Y-%m-%d %H:%M"),
                campaign.last_execution_at.strftime("%Y-%m-%d %H:%M")
                if campaign.last_execution_at
                else "-",
                (campaign.last_execution_result[:100] + "...")
                if campaign.last_execution_result
                and len(campaign.last_execution_result) > 100
                else (campaign.last_execution_result or "-"),
            ]
            data.append(row)

        return data
