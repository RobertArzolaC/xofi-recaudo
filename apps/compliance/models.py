from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.compliance import choices
from apps.core import choices as core_choices
from apps.core import models as core_models


class BaseCompliancePayment(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Abstract base model for all compliance-related payments."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        help_text=_("Partner making the payment."),
    )
    amount = models.DecimalField(
        _("Amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Payment amount."),
    )
    due_date = models.DateField(
        _("Due Date"),
        help_text=_("Date when the payment is due."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.ComplianceStatus.choices,
        default=choices.ComplianceStatus.PENDING,
        help_text=_("Status of the payment."),
    )
    payments = GenericRelation(
        "payments.PaymentConceptAllocation",
        help_text=_("Payment allocations for this compliance obligation."),
    )

    class Meta:
        abstract = True

    @property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        return (
            self.status
            in [
                choices.ComplianceStatus.PENDING,
                choices.ComplianceStatus.PARTIAL,
            ]
            and self.due_date < timezone.now().date()
        )

    @property
    def days_overdue(self) -> int:
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def total_paid(self) -> Decimal:
        """Calculate total amount paid."""
        from apps.payments import choices as payment_choices

        return sum(
            allocation.amount_applied
            for allocation in self.payments.filter(
                payment__status=payment_choices.PaymentStatus.PAID
            )
        )

    @property
    def remaining_balance(self) -> Decimal:
        """Calculate remaining balance to be paid."""
        return max(self.amount - self.total_paid, Decimal("0.00"))

    @property
    def is_fully_paid(self) -> bool:
        """Check if obligation is fully paid."""
        return self.total_paid >= self.amount

    @property
    def period_display(self) -> str:
        """Get human-readable period."""
        if not hasattr(self, "period_month") or not hasattr(
            self, "period_year"
        ):
            return "N/A"
        return f"{self.get_month_display()} {self.period_year}"

    def get_month_display(self) -> str:
        """Get month name from month number."""

        return core_choices.Month(self.period_month).label


class Contribution(BaseCompliancePayment):
    period_year = models.PositiveIntegerField(
        _("Period Year"),
        help_text=_("Year of the contribution period."),
    )
    period_month = models.PositiveIntegerField(
        _("Period Month"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("Month of the contribution period."),
    )

    class Meta:
        managed = False
        verbose_name = _("Contribution")
        verbose_name_plural = _("Contributions")
        ordering = ["-period_year", "-period_month", "partner"]
        unique_together = ["partner", "period_year", "period_month"]

    def __str__(self) -> str:
        return f"{self.partner.full_name} - {_('Contribution')} - {self.period_year}/{self.period_month:02d} - ${self.amount:,.2f}"


class SocialSecurity(BaseCompliancePayment):
    period_year = models.PositiveIntegerField(
        _("Period Year"),
        help_text=_("Year of the social security period."),
    )
    period_month = models.PositiveIntegerField(
        _("Period Month"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("Month of the social security period."),
    )

    class Meta:
        managed = False
        verbose_name = _("Social Security")
        verbose_name_plural = _("Social Security")
        ordering = ["-period_year", "-period_month", "partner"]
        unique_together = ["partner", "period_year", "period_month"]

    def __str__(self) -> str:
        return f"{self.partner.full_name} - {_('Social Security')} - {self.period_year}/{self.period_month:02d} - ${self.amount:,.2f}"


class Penalty(BaseCompliancePayment):
    penalty_type = models.CharField(
        _("Penalty Type"),
        max_length=25,
        choices=choices.PenaltyType.choices,
        help_text=_("Type of penalty."),
    )
    issue_date = models.DateField(
        _("Issue Date"),
        auto_now_add=True,
        help_text=_("Date when the penalty was issued."),
    )
    description = models.TextField(
        _("Description"),
        help_text=_("Description of the violation or reason for penalty."),
    )

    class Meta:
        managed = False
        verbose_name = _("Penalty")
        verbose_name_plural = _("Penalties")
        ordering = ["-issue_date"]

    def __str__(self) -> str:
        return f"{self.partner.full_name} - {self.get_penalty_type_display()} - ${self.amount:,.2f}"
