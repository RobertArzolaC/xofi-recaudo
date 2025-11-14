from typing import Any, List

from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.credits.models import Installment
from apps.payments.models import Payment
from apps.reports.generators.base import BaseReportGenerator


class CollectionRecoveryReportGenerator(BaseReportGenerator):
    """
    Generate recovery report showing collected amounts and recovery rates.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered payments queryset."""
        queryset = Payment.objects.select_related("partner").filter(
            status="paid"
        )

        # Apply filters
        date_from = self.filters.get("date_from")
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)

        date_to = self.filters.get("date_to")
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)

        payment_method = self.filters.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset.order_by("-payment_date")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Payment Number"),
            _("Payment Date"),
            _("Partner Document"),
            _("Partner Name"),
            _("Amount Collected"),
            _("Payment Method"),
            _("Reference Number"),
            _("Amount Allocated"),
            _("Unallocated Amount"),
            _("Notes"),
            _("Created Date"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        for payment in queryset:
            allocated = payment.total_allocated
            unallocated = payment.unallocated_amount

            row = [
                payment.payment_number,
                payment.payment_date.strftime("%Y-%m-%d"),
                payment.partner.document_number,
                payment.partner.full_name,
                float(payment.amount),
                payment.get_payment_method_display(),
                payment.reference_number or "-",
                float(allocated),
                float(unallocated),
                payment.notes or "-",
                payment.created.strftime("%Y-%m-%d %H:%M"),
            ]
            data.append(row)

        return data


class CollectionPortfolioAgingReportGenerator(BaseReportGenerator):
    """
    Generate portfolio aging report showing installment aging buckets.
    """

    def get_queryset(self) -> QuerySet:
        """Get overdue installments queryset."""
        queryset = Installment.objects.select_related(
            "credit", "credit__partner", "credit__product"
        ).filter(status__in=["PENDING", "PARTIAL"])

        # Apply filters
        partner_id = self.filters.get("partner_id")
        if partner_id:
            queryset = queryset.filter(credit__partner_id=partner_id)

        product_id = self.filters.get("product_id")
        if product_id:
            queryset = queryset.filter(credit__product_id=product_id)

        return queryset.order_by("due_date", "credit__partner__document_number")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Partner Document"),
            _("Partner Name"),
            _("Credit ID"),
            _("Product"),
            _("Installment Number"),
            _("Due Date"),
            _("Installment Amount"),
            _("Principal Amount"),
            _("Interest Amount"),
            _("Outstanding Balance"),
            _("Days Overdue"),
            _("Aging Bucket"),
            _("Status"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []
        today = timezone.now().date()

        for installment in queryset:
            # Calculate days overdue
            days_overdue = (
                (today - installment.due_date).days
                if installment.due_date < today
                else 0
            )

            # Determine aging bucket
            if days_overdue <= 0:
                aging_bucket = _("Current")
            elif days_overdue <= 30:
                aging_bucket = "1-30 days"
            elif days_overdue <= 60:
                aging_bucket = "31-60 days"
            elif days_overdue <= 90:
                aging_bucket = "61-90 days"
            elif days_overdue <= 180:
                aging_bucket = "91-180 days"
            else:
                aging_bucket = "180+ days"

            # Calculate outstanding (for partial payments)
            outstanding = installment.installment_amount
            # If there are allocations, we'd need to calculate remaining
            # For now using full amount

            row = [
                installment.credit.partner.document_number,
                installment.credit.partner.full_name,
                installment.credit.id,
                installment.credit.product.name,
                installment.installment_number,
                installment.due_date.strftime("%Y-%m-%d"),
                float(installment.installment_amount),
                float(installment.principal_amount),
                float(installment.interest_amount),
                float(outstanding),
                days_overdue,
                aging_bucket,
                installment.get_status_display(),
            ]
            data.append(row)

        return data


class CollectionContactabilityReportGenerator(BaseReportGenerator):
    """
    Generate contactability report based on campaign notifications.
    Shows contact attempts and success rates by partner and channel.
    """

    def get_queryset(self) -> QuerySet:
        """Get filtered campaign notifications queryset."""
        from apps.campaigns.models import CampaignNotification

        queryset = CampaignNotification.objects.select_related(
            "campaign", "partner"
        )

        # Apply filters
        date_from = self.filters.get("date_from")
        if date_from:
            queryset = queryset.filter(created__gte=date_from)

        date_to = self.filters.get("date_to")
        if date_to:
            queryset = queryset.filter(created__lte=date_to)

        channel = self.filters.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        partner_id = self.filters.get("partner_id")
        if partner_id:
            queryset = queryset.filter(partner_id=partner_id)

        return queryset.order_by("-created")

    def get_headers(self) -> List[str]:
        """Return column headers."""
        return [
            _("Partner Document"),
            _("Partner Name"),
            _("Campaign"),
            _("Notification Type"),
            _("Channel"),
            _("Status"),
            _("Recipient Email"),
            _("Recipient Phone"),
            _("Scheduled At"),
            _("Sent At"),
            _("Delivery Time (minutes)"),
            _("Error Message"),
            _("Created Date"),
        ]

    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """Transform queryset into report data."""
        data = []

        for notification in queryset:
            # Calculate delivery time
            delivery_time = "-"
            if notification.scheduled_at and notification.sent_at:
                delta = notification.sent_at - notification.scheduled_at
                delivery_time = int(delta.total_seconds() / 60)

            row = [
                notification.partner.document_number,
                notification.partner.full_name,
                notification.campaign.name,
                notification.get_notification_type_display(),
                notification.get_channel_display(),
                notification.get_status_display(),
                notification.recipient_email or "-",
                notification.recipient_phone or "-",
                notification.scheduled_at.strftime("%Y-%m-%d %H:%M")
                if notification.scheduled_at
                else "-",
                notification.sent_at.strftime("%Y-%m-%d %H:%M")
                if notification.sent_at
                else "-",
                delivery_time,
                notification.error_message or "-",
                notification.created.strftime("%Y-%m-%d %H:%M"),
            ]
            data.append(row)

        return data
