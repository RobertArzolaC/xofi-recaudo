from django.db import models

from apps.payments.querysets import PaymentQuerySet, PaymentConceptAllocationQuerySet


class PaymentManager(models.Manager):
    """Custom manager for Payment model."""

    def get_queryset(self):
        return PaymentQuerySet(self.model, using=self._db)

    def for_partner(self, partner):
        """Get all payments for a specific partner."""
        return self.get_queryset().for_partner(partner)

    def by_date_range(self, start_date, end_date):
        """Get payments made within a specific date range."""
        return self.get_queryset().by_date_range(start_date, end_date)

    def paid(self):
        """Get all paid payments."""
        return self.get_queryset().paid()

    def cancelled(self):
        """Get all cancelled payments."""
        return self.get_queryset().cancelled()

    def refunded(self):
        """Get all refunded payments."""
        return self.get_queryset().refunded()

    def fully_allocated(self):
        """Get payments that are fully allocated to concepts."""
        return self.get_queryset().fully_allocated()

    def partially_allocated(self):
        """Get payments that are partially allocated to concepts."""
        return self.get_queryset().partially_allocated()

    def unallocated(self):
        """Get payments that have not been allocated to any concepts."""
        return self.get_queryset().unallocated()

    def summary_by_partner(self):
        """Get payment summary grouped by partner."""
        return self.get_queryset().summary_by_partner()

    def summary_by_partner_aggregate(self, partner):
        """Get payment summary for a specific partner."""
        return self.get_queryset().summary_by_partner_aggregate(partner)


class PaymentConceptAllocationManager(models.Manager):
    """Custom manager for PaymentConceptAllocation model."""

    def get_queryset(self):
        return PaymentConceptAllocationQuerySet(self.model, using=self._db)

    def for_payment(self, payment):
        """Get allocations for a specific payment."""
        return self.get_queryset().for_payment(payment)

    def for_concept_type(self, model_class):
        """Get allocations for a specific concept type."""
        return self.get_queryset().for_concept_type(model_class)

    def allocate_payment_to_concept(
        self,
        payment,
        concept_object,
        amount_applied=None,
        allocation_type="FULL",
        notes="",
    ):
        """Allocate a payment (or part of it) to a specific concept."""
        from django.contrib.contenttypes.models import ContentType

        if amount_applied is None:
            amount_applied = payment.amount

        # Validate allocation amount
        if amount_applied > payment.unallocated_amount:
            raise ValueError("Cannot allocate more than the unallocated payment amount")

        content_type = ContentType.objects.get_for_model(concept_object.__class__)

        return self.create(
            payment=payment,
            content_type=content_type,
            object_id=concept_object.id,
            amount_applied=amount_applied,
            allocation_type=allocation_type,
            notes=notes,
        )

    def summary_by_concept_type(self):
        """Get allocation summary grouped by concept type."""
        return self.get_queryset().summary_by_concept_type()

    def summary_by_allocation_type(self):
        """Get allocation summary grouped by allocation type."""
        return self.get_queryset().summary_by_allocation_type()
