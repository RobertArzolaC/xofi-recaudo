from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.payments import choices, managers


class Payment(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent actual payments made by partners."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="payments",
        help_text=_("Partner making the payment."),
    )
    payment_number = models.CharField(
        _("Payment Number"),
        max_length=50,
        help_text=_("Unique payment identifier or number."),
    )
    payment_date = models.DateField(
        _("Payment Date"),
        help_text=_("Date when the payment was actually made."),
    )
    amount = models.DecimalField(
        _("Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount paid."),
    )
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=20,
        choices=choices.PaymentMethod.choices,
        default=choices.PaymentMethod.CASH,
        help_text=_("Method used for the payment."),
    )
    reference_number = models.CharField(
        _("Reference Number"),
        max_length=100,
        blank=True,
        help_text=_("Bank reference, check number, or transaction ID."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.PaymentStatus.choices,
        default=choices.PaymentStatus.PAID,
        help_text=_("Status of this payment."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about the payment."),
    )
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional data specific to the payment concept."),
    )

    class Meta:
        managed = False
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-payment_date", "-created"]
        indexes = [
            models.Index(fields=["partner"]),
            models.Index(fields=["payment_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Payment #{self.payment_number} - {self.partner.full_name} - ${self.amount:,.2f}"

    @property
    def total_allocated(self) -> Decimal:
        """Calculate total amount allocated to concepts."""

        result = self.concept_allocations.aggregate(total=Sum("amount_applied"))
        return result["total"] or Decimal("0.00")

    @property
    def unallocated_amount(self) -> Decimal:
        """Calculate amount not yet allocated to concepts."""
        return max(self.amount - self.total_allocated, Decimal("0.00"))

    @property
    def is_fully_allocated(self) -> bool:
        """Check if payment is fully allocated to concepts."""
        return self.unallocated_amount == Decimal("0.00")

    # Custom manager
    objects = managers.PaymentManager()

    def allocate_to_concept(self, concept_object, amount=None, notes=""):
        """Allocate this payment (or part of it) to a specific concept."""
        if amount is None:
            amount = self.unallocated_amount

        if amount <= 0:
            raise ValueError("Allocation amount must be greater than 0")

        if amount > self.unallocated_amount:
            raise ValueError("Cannot allocate more than the unallocated amount")

        allocation_type = (
            choices.AllocationStatus.FULL
            if amount == self.unallocated_amount
            else choices.AllocationStatus.PARTIAL
        )

        return PaymentConceptAllocation.objects.allocate_payment_to_concept(
            payment=self,
            concept_object=concept_object,
            amount_applied=amount,
            allocation_type=allocation_type,
            notes=notes,
        )

    def can_be_allocated_to_concept(self, amount=None):
        """Check if this payment can be allocated to a specific concept."""
        if amount is None:
            amount = self.unallocated_amount

        if amount <= 0:
            return False, "Allocation amount must be greater than 0"

        if amount > self.unallocated_amount:
            return False, "Cannot allocate more than the unallocated amount"

        return True, "Allocation is valid"

    @classmethod
    def create_payment(
        cls,
        partner,
        amount,
        payment_method=None,
        payment_date=None,
        payment_number=None,
        reference_number="",
        notes="",
        metadata=None,
    ):
        """Create a payment record for a partner."""
        if payment_date is None:
            payment_date = timezone.now().date()

        if payment_method is None:
            payment_method = choices.PaymentMethod.CASH

        if not payment_number:
            # Generate a simple payment number
            payment_number = (
                f"PAY-{partner.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            )

        if metadata is None:
            metadata = {}

        return cls.objects.create(
            partner=partner,
            payment_number=payment_number,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            metadata=metadata,
        )


class PaymentConceptAllocation(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent allocation of a payment to specific concepts (installments, obligations, etc.)."""

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="concept_allocations",
        help_text=_("Payment being allocated."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=_(
            "Type of concept receiving the payment (Installment, Contribution, Penalty, etc.)."
        ),
    )
    object_id = models.PositiveIntegerField(
        help_text=_("ID of the concept receiving the payment."),
    )
    concept_object = GenericForeignKey("content_type", "object_id")
    amount_applied = models.DecimalField(
        _("Amount Applied"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount from the payment applied to this concept."),
    )
    application_date = models.DateField(
        _("Application Date"),
        auto_now_add=True,
        help_text=_("Date when the payment was applied to this concept."),
    )
    allocation_type = models.CharField(
        _("Allocation Type"),
        max_length=20,
        choices=choices.AllocationStatus.choices,
        default=choices.AllocationStatus.FULL,
        help_text=_("Type of allocation."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about this payment allocation."),
    )

    class Meta:
        managed = False
        verbose_name = _("Payment Concept Allocation")
        verbose_name_plural = _("Payment Concept Allocations")
        ordering = ["payment", "application_date"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["payment", "application_date"]),
        ]

    def __str__(self) -> str:
        return f"Payment #{self.payment.payment_number} → {self.concept_object} - ${self.amount_applied:,.2f}"

    def clean(self):
        """Validate payment allocation."""
        if self.payment_id and self.amount_applied:
            if self.amount_applied > self.payment.amount:
                raise ValidationError(
                    _("Cannot allocate more than the payment amount.")
                )

    # Custom manager
    objects = managers.PaymentConceptAllocationManager()
