"""
Report generators for Payment-related reports.

This module contains report generators for payment links and promises.
"""

from typing import Any, List

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from apps.payments.models import MagicPaymentLink
from apps.reports.generators.base import BaseReportGenerator


class PaymentPromisesTrackingReportGenerator(BaseReportGenerator):
    """
    Generate payment promises tracking report.

    Note: This is a placeholder implementation as payment promises model
    doesn't exist yet. When implemented, it should track:
    - Promise date
    - Promised amount
    - Fulfillment status
    - Actual payment details
    """

    def get_queryset(self) -> QuerySet:
        """Get payment promises queryset."""
        # TODO: Replace with actual PaymentPromise model when available
        # For now, using magic links as proxy for promised payments
        from apps.payments.models import MagicPaymentLink

        queryset = MagicPaymentLink.objects.select_related("partner", "payment")

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

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Partner Document"),
            _("Partner Name"),
            _("Link Name"),
            _("Promised Amount"),
            _("Status"),
            _("Created Date"),
            _("Expires At"),
            _("Used At"),
            _("Payment Reference"),
            _("Actual Amount Paid"),
            _("Fulfillment Rate %"),
            _("Days to Fulfill"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        for link in queryset:
            # Calculate fulfillment metrics
            actual_paid = float(link.payment.amount) if link.payment else 0
            fulfillment_rate = (
                (actual_paid / float(link.amount) * 100) if link.amount > 0 else 0
            )

            # Calculate days to fulfill
            days_to_fulfill = "-"
            if link.used_at:
                delta = link.used_at - link.created
                days_to_fulfill = delta.days

            row = [
                link.partner.document_number,
                link.partner.full_name,
                link.name,
                float(link.amount),
                link.get_status_display(),
                link.created.strftime("%Y-%m-%d %H:%M"),
                link.expires_at.strftime("%Y-%m-%d %H:%M"),
                link.used_at.strftime("%Y-%m-%d %H:%M") if link.used_at else "-",
                link.payment.payment_number if link.payment else "-",
                actual_paid,
                round(fulfillment_rate, 2),
                days_to_fulfill,
            ]
            data.append(row)

        return data


class MagicPaymentLinksReportGenerator(BaseReportGenerator):
    """
    Generate Magic Payment Links report showing usage and conversion.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered magic payment links queryset."""
        queryset = MagicPaymentLink.objects.select_related("partner", "payment")

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

        source = self.filters.get("source")
        if source:
            queryset = queryset.filter(source=source)

        partner_id = self.filters.get("partner_id")
        if partner_id:
            queryset = queryset.filter(partner_id=partner_id)

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Link Name"),
            _("Partner Document"),
            _("Partner Name"),
            _("Token"),
            _("Total Amount"),
            _("Status"),
            _("Source"),
            _("Created Date"),
            _("Expires At"),
            _("Used At"),
            _("Payment Reference"),
            _("Amount Paid"),
            _("Is Expired"),
            _("Conversion Time (hours)"),
            _("Debt Concepts Count"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        for link in queryset:
            # Check if expired
            from django.utils import timezone

            is_expired = link.expires_at < timezone.now() if link.status != "used" else False

            # Calculate conversion time
            conversion_time = "-"
            if link.used_at:
                delta = link.used_at - link.created
                conversion_time = round(delta.total_seconds() / 3600, 2)

            # Count debt concepts
            debt_concepts = link.metadata.get("debts", []) if link.metadata else []
            concepts_count = len(debt_concepts)

            row = [
                link.name,
                link.partner.document_number,
                link.partner.full_name,
                link.token,
                float(link.amount),
                link.get_status_display(),
                link.get_source_display(),
                link.created.strftime("%Y-%m-%d %H:%M"),
                link.expires_at.strftime("%Y-%m-%d %H:%M"),
                link.used_at.strftime("%Y-%m-%d %H:%M") if link.used_at else "-",
                link.payment.payment_number if link.payment else "-",
                float(link.payment.amount) if link.payment else 0,
                "Yes" if is_expired else "No",
                conversion_time,
                concepts_count,
            ]
            data.append(row)

        return data
