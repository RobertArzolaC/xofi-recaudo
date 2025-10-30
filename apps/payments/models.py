import secrets
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
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


class PaymentReceipt(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent payment receipts/vouchers uploaded by partners."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="payment_receipts",
        help_text=_("Partner who uploaded the receipt."),
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        related_name="receipts",
        null=True,
        blank=True,
        help_text=_("Associated payment if linked."),
    )
    receipt_file = models.FileField(
        _("Receipt File"),
        upload_to="payment_receipts/%Y/%m/%d/",
        help_text=_("Uploaded receipt file (PDF, JPG, PNG)."),
    )
    amount = models.DecimalField(
        _("Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount shown on the receipt."),
    )
    payment_date = models.DateField(
        _("Payment Date"),
        help_text=_("Date when the payment was made according to the receipt."),
    )
    status = models.CharField(
        _("Validation Status"),
        max_length=20,
        choices=choices.ReceiptStatus.choices,
        default=choices.ReceiptStatus.PENDING,
        help_text=_("Validation status of the receipt."),
    )
    validation_notes = models.TextField(
        _("Validation Notes"),
        blank=True,
        help_text=_("Notes from the employee who validated the receipt."),
    )
    validated_by = models.ForeignKey(
        "team.Employee",
        on_delete=models.SET_NULL,
        related_name="validated_receipts",
        null=True,
        blank=True,
        help_text=_("Employee who validated this receipt."),
    )
    validated_at = models.DateTimeField(
        _("Validated At"),
        null=True,
        blank=True,
        help_text=_("Date and time when the receipt was validated."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about the receipt."),
    )

    class Meta:
        verbose_name = _("Payment Receipt")
        verbose_name_plural = _("Payment Receipts")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["partner"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_date"]),
            models.Index(fields=["-created"]),
        ]

    def __str__(self) -> str:
        return f"Receipt for {self.partner.full_name} - ${self.amount:,.2f} - {self.get_status_display()}"

    def approve(self, employee, notes=""):
        """Approve the receipt."""
        if self.status == choices.ReceiptStatus.PENDING:
            self.status = choices.ReceiptStatus.APPROVED
            self.validated_by = employee
            self.validated_at = timezone.now()
            self.validation_notes = notes
            self.save(
                update_fields=[
                    "status",
                    "validated_by",
                    "validated_at",
                    "validation_notes",
                ]
            )
            return True
        return False

    def reject(self, employee, notes=""):
        """Reject the receipt."""
        if self.status == choices.ReceiptStatus.PENDING:
            self.status = choices.ReceiptStatus.REJECTED
            self.validated_by = employee
            self.validated_at = timezone.now()
            self.validation_notes = notes
            self.save(
                update_fields=[
                    "status",
                    "validated_by",
                    "validated_at",
                    "validation_notes",
                ]
            )
            return True
        return False

    @property
    def is_pending(self) -> bool:
        """Check if receipt is pending validation."""
        return self.status == choices.ReceiptStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if receipt is approved."""
        return self.status == choices.ReceiptStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        """Check if receipt is rejected."""
        return self.status == choices.ReceiptStatus.REJECTED


class MagicPaymentLink(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent Magic Payment Links for partners.

    A magic link can include multiple debt concepts (installments, contributions, etc.)
    that will be paid together in a single payment session.
    """

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="magic_payment_links",
        help_text=_("Partner for whom this link was created."),
    )
    token = models.CharField(
        _("Token"),
        max_length=12,
        unique=True,
        help_text=_("Unique short token for the payment link URL."),
    )
    amount = models.DecimalField(
        _("Total Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Total amount to be paid (sum of all included debts)."),
    )
    expires_at = models.DateTimeField(
        _("Expires At"),
        help_text=_("Date and time when this link expires."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.MagicLinkStatus.choices,
        default=choices.MagicLinkStatus.ACTIVE,
        help_text=_("Status of the payment link."),
    )
    used_at = models.DateTimeField(
        _("Used At"),
        null=True,
        blank=True,
        help_text=_("Date and time when this link was used for payment."),
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        related_name="magic_links",
        null=True,
        blank=True,
        help_text=_("Payment associated with this link if used."),
    )
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Additional metadata including debt concepts: "
            "{'debts': [{'type': 'installment', 'id': 123, 'amount': 387.00}, ...]}"
        ),
    )
    source = models.CharField(
        _("Source"),
        max_length=20,
        choices=choices.MagicLinkSource.choices,
        default=choices.MagicLinkSource.MANUAL,
        help_text=_("Source or campaign that generated this link."),
    )

    class Meta:
        verbose_name = _("Magic Payment Link")
        verbose_name_plural = _("Magic Payment Links")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["partner"]),
            models.Index(fields=["token"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["-created"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.partner.full_name}"

    def save(self, *args, **kwargs):
        """Generate unique token if not set."""
        if not self.token:
            self.token = self.generate_unique_token()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_token(length=8):
        """Generate a unique short token for the payment link."""
        while True:
            token = secrets.token_urlsafe(length)[:length]
            if not MagicPaymentLink.objects.filter(token=token).exists():
                return token

    @property
    def is_active(self) -> bool:
        """Check if link is active and not expired."""
        return (
            self.status == choices.MagicLinkStatus.ACTIVE
            and self.expires_at > timezone.now()
        )

    @property
    def is_expired(self) -> bool:
        """Check if link has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if link has been used."""
        return self.status == choices.MagicLinkStatus.USED

    @property
    def debt_count(self) -> int:
        """Get the number of debts included in this link."""
        return len(self.metadata.get("debts", []))

    def get_public_url(self) -> str:
        """Get the public URL for this payment link."""
        return reverse(
            "apps.payments:magic-link-public", kwargs={"token": self.token}
        )

    def get_full_url(self, request=None) -> str:
        """Get the full absolute URL including domain."""
        url = reverse(
            "apps.payments:magic-link-public", kwargs={"token": self.token}
        )
        if request:
            return request.build_absolute_uri(url)
        return url

    def mark_as_used(self, payment=None):
        """Mark the link as used."""
        self.status = choices.MagicLinkStatus.USED
        self.used_at = timezone.now()
        if payment:
            self.payment = payment
        self.save(update_fields=["status", "used_at", "payment"])

    def mark_as_expired(self):
        """Mark the link as expired."""
        if self.status == choices.MagicLinkStatus.ACTIVE:
            self.status = choices.MagicLinkStatus.EXPIRED
            self.save(update_fields=["status"])

    def mark_as_cancelled(self):
        """Mark the link as cancelled."""
        if self.status == choices.MagicLinkStatus.ACTIVE:
            self.status = choices.MagicLinkStatus.CANCELLED
            self.save(update_fields=["status"])

    def check_and_update_expiration(self):
        """Check if link is expired and update status accordingly."""
        if self.is_expired and self.status == choices.MagicLinkStatus.ACTIVE:
            self.mark_as_expired()
