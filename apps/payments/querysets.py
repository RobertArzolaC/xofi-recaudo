from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone

from apps.payments import choices


class PaymentQuerySet(models.QuerySet):
    """Custom QuerySet for Payment model with useful filtering methods."""

    def for_partner(self, partner):
        """Filter payments for a specific partner."""
        return self.filter(partner=partner)

    def by_date_range(self, start_date, end_date):
        """Filter payments made within a specific date range."""
        return self.filter(payment_date__range=[start_date, end_date])

    def paid(self):
        """Filter paid payments."""
        return self.filter(status=choices.PaymentStatus.PAID)

    def cancelled(self):
        """Filter cancelled payments."""
        return self.filter(status=choices.PaymentStatus.CANCELLED)

    def refunded(self):
        """Filter refunded payments."""
        return self.filter(status=choices.PaymentStatus.REFUNDED)

    def fully_allocated(self):
        """Filter payments that are fully allocated to concepts."""
        return self.filter(
            id__in=models.Subquery(
                self.annotate(
                    total_allocated=models.Sum("concept_allocations__amount_applied")
                )
                .filter(total_allocated__gte=models.F("amount"))
                .values("id")
            )
        )

    def partially_allocated(self):
        """Filter payments that are partially allocated to concepts."""
        return self.filter(
            id__in=models.Subquery(
                self.annotate(
                    total_allocated=models.Sum("concept_allocations__amount_applied")
                )
                .filter(
                    total_allocated__gt=0,
                    total_allocated__lt=models.F("amount"),
                )
                .values("id")
            )
        )

    def unallocated(self):
        """Filter payments that have not been allocated to any concepts."""
        return self.filter(concept_allocations__isnull=True)

    def summary_by_partner(self):
        """Get payment summary grouped by partner."""
        return (
            self.values("partner")
            .annotate(
                total_amount=Sum("amount"),
                count=Count("id"),
                avg_amount=models.Avg("amount"),
            )
            .order_by("partner")
        )

    def summary_by_partner_aggregate(self, partner):
        """Get payment summary for a specific partner using aggregation."""
        return self.filter(partner=partner).aggregate(
            total_amount=Sum("amount"),
            count=Count("id"),
            avg_amount=models.Avg("amount"),
        )


class PaymentConceptAllocationQuerySet(models.QuerySet):
    """Custom QuerySet for PaymentConceptAllocation model."""

    def for_payment(self, payment):
        """Filter allocations for a specific payment."""
        return self.filter(payment=payment)

    def for_concept_type(self, model_class):
        """Filter allocations for a specific concept type."""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(model_class)
        return self.filter(content_type=content_type)

    def for_concept_type_by_app_model(self, app_label, model_name):
        """Filter allocations for a specific concept type by app and model name."""
        return self.filter(
            content_type__app_label=app_label, content_type__model=model_name
        )

    def full_payments(self):
        """Filter full payment allocations."""
        return self.filter(allocation_type=choices.AllocationStatus.FULL)

    def partial_payments(self):
        """Filter partial payment allocations."""
        return self.filter(allocation_type=choices.AllocationStatus.PARTIAL)

    def overpayments(self):
        """Filter overpayment allocations."""
        return self.filter(allocation_type=choices.AllocationStatus.OVERPAYMENT)

    def recent(self, days=30):
        """Filter allocations from the last N days."""
        cutoff_date = timezone.now().date() - timezone.timedelta(days=days)
        return self.filter(application_date__gte=cutoff_date)

    def for_installments(self):
        """Filter allocations for installments."""
        return self.for_concept_type_by_app_model("credits", "installment")

    def for_contributions(self):
        """Filter allocations for contributions."""
        return self.for_concept_type_by_app_model("compliance", "contribution")

    def for_social_security(self):
        """Filter allocations for social security."""
        return self.for_concept_type_by_app_model("compliance", "socialsecurity")

    def for_penalties(self):
        """Filter allocations for penalties."""
        return self.for_concept_type_by_app_model("compliance", "penalty")

    def for_compliance(self):
        """Filter allocations for all compliance-related concepts."""
        return self.filter(
            content_type__app_label="compliance",
            content_type__model__in=[
                "contribution",
                "socialsecurity",
                "penalty",
            ],
        )

    def summary_by_concept_type(self):
        """Get allocation summary grouped by concept type."""
        return (
            self.values("content_type__app_label", "content_type__model")
            .annotate(
                total_allocated=Sum("amount_applied"),
                count=Count("id"),
                avg_allocation=models.Avg("amount_applied"),
            )
            .order_by("content_type__app_label", "content_type__model")
        )

    def summary_by_allocation_type(self):
        """Get allocation summary grouped by allocation type."""
        return (
            self.values("allocation_type")
            .annotate(
                total_allocated=Sum("amount_applied"),
                count=Count("id"),
                avg_allocation=models.Avg("amount_applied"),
            )
            .order_by("allocation_type")
        )

    def total_allocated_amount(self):
        """Get total amount allocated across all allocations in queryset."""
        result = self.aggregate(total=Sum("amount_applied"))
        return result["total"] or 0
