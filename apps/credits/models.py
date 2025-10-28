from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.credits import choices, managers, utils
from apps.payments import choices as payment_choices


class ProductType(
    core_models.BaseUserTracked,
    core_models.NameDescription,
    TimeStampedModel,
):
    """Model to represent a product type for credits."""

    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this product type is active."),
    )

    class Meta:
        verbose_name = _("Product Type")
        verbose_name_plural = _("Product Types")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(
    core_models.BaseUserTracked,
    core_models.NameDescription,
    TimeStampedModel,
):
    """Model to represent a credit product."""

    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="products",
        help_text=_("Product type this product belongs to."),
    )
    min_amount = models.DecimalField(
        _("Minimum Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Minimum credit amount."),
    )
    max_amount = models.DecimalField(
        _("Maximum Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Maximum credit amount."),
    )
    min_interest_rate = models.DecimalField(
        _("Minimum Interest Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text=_("Minimum annual interest rate percentage."),
    )
    max_interest_rate = models.DecimalField(
        _("Maximum Interest Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text=_("Maximum annual interest rate percentage."),
    )
    interest_type = models.CharField(
        _("Interest Type"),
        max_length=10,
        choices=choices.InterestType.choices,
        default=choices.InterestType.FIXED,
        help_text=_("Type of interest rate."),
    )
    min_term_duration = models.PositiveIntegerField(
        _("Minimum Term Duration"),
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text=_("Minimum duration in months."),
    )
    max_term_duration = models.PositiveIntegerField(
        _("Maximum Term Duration"),
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text=_("Maximum duration in months."),
    )
    payment_frequency = models.CharField(
        _("Payment Frequency"),
        max_length=15,
        choices=choices.PaymentFrequency.choices,
        default=choices.PaymentFrequency.MONTHLY,
        help_text=_("How often payments are due."),
    )
    min_delinquency_rate = models.DecimalField(
        _("Minimum Delinquency Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        default=Decimal("0.00"),
        help_text=_("Minimum delinquency rate percentage for overdue payments."),
    )
    max_delinquency_rate = models.DecimalField(
        _("Maximum Delinquency Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        default=Decimal("0.00"),
        help_text=_("Maximum delinquency rate percentage for overdue payments."),
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this product is active."),
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["product_type", "name"]

    def __str__(self) -> str:
        return f"{self.product_type.name} - {self.name}"


class Credit(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a credit/loan."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="credits",
        help_text=_("Partner who requested the credit."),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="credits",
        help_text=_("Product this credit is based on."),
    )
    amount = models.DecimalField(
        _("Credit Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Total amount of the credit."),
    )
    interest_rate = models.DecimalField(
        _("Interest Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text=_("Annual interest rate percentage."),
    )
    term_duration = models.PositiveIntegerField(
        _("Term Duration"),
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text=_("Duration of the credit in months."),
    )
    delinquency_rate = models.DecimalField(
        _("Delinquency Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        default=Decimal("0.00"),
        help_text=_("Delinquency rate percentage for overdue payments."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.CreditStatus.choices,
        default=choices.CreditStatus.PENDING,
        help_text=_("Current status of the credit."),
    )
    application_date = models.DateField(
        _("Application Date"),
        auto_now_add=True,
        help_text=_("Date when the credit was applied for."),
    )
    approval_date = models.DateField(
        _("Approval Date"),
        null=True,
        blank=True,
        help_text=_("Date when the credit was approved."),
    )
    disbursement_date = models.DateField(
        _("Disbursement Date"),
        null=True,
        blank=True,
        help_text=_("Date when the credit was disbursed."),
    )
    payment_frequency = models.CharField(
        _("Payment Frequency"),
        max_length=15,
        choices=choices.PaymentFrequency.choices,
        default=choices.PaymentFrequency.MONTHLY,
        help_text=_("How often payments are due for this credit."),
    )
    payment_amount = models.DecimalField(
        _("Payment Amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Calculated payment amount based on frequency."),
    )
    outstanding_balance = models.DecimalField(
        _("Outstanding Balance"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Current outstanding balance."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about the credit."),
    )
    application = models.OneToOneField(
        "CreditApplication",
        on_delete=models.SET_NULL,
        related_name="credit",
        null=True,
        blank=True,
        help_text=_("Credit application that originated this credit."),
    )
    current_version = models.PositiveIntegerField(
        _("Current Version"),
        default=1,
        help_text=_("Current version number of the credit."),
    )

    # Generic relation to status history
    status_history = GenericRelation(
        "core.StatusHistory",
        help_text=_("History of status changes for this credit."),
    )

    objects = managers.CreditManager()

    class Meta:
        verbose_name = _("Credit")
        verbose_name_plural = _("Credits")
        ordering = ["-created"]
        permissions = [
            ("change_credit_status", "Can change credit status"),
            ("approve_credit", "Can approve credits"),
            ("reject_credit", "Can reject credits"),
        ]

    def __str__(self) -> str:
        return (
            f"{self.partner.full_name} - {self.product.name} - {self.amount:,.2f} PEN"
        )

    def change_status(self, new_status: str, user, note: str = ""):
        """Change the status and create a history entry."""
        if self.status == new_status:
            return False

        # Store the previous status before changing it
        previous_status = self.status

        # Update the current status
        self.status = new_status
        self.modified_by = user

        # Set approval_date when status changes to APPROVED
        if new_status == choices.CreditStatus.APPROVED and not self.approval_date:
            self.approval_date = timezone.now().date()

        self.save()

        # Create status history entry
        core_models.StatusHistory.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            status=new_status,
            previous_status=previous_status,
            note=note,
            created_by=user,
            modified_by=user,
        )
        return True

    def approve(self, user=None, note: str = ""):
        """Approve the credit."""
        if self.status == choices.CreditStatus.PENDING:
            return self.change_status(choices.CreditStatus.APPROVED, user, note)
        return False

    def reject(self, user=None, note: str = ""):
        """Reject the credit."""
        if self.status == choices.CreditStatus.PENDING:
            return self.change_status(choices.CreditStatus.REJECTED, user, note)
        return False

    def cancel(self, user=None, note: str = ""):
        """Cancel the credit."""
        if self.status not in [
            choices.CreditStatus.COMPLETED,
            choices.CreditStatus.DEFAULTED,
            choices.CreditStatus.REFINANCED,
        ]:
            return self.change_status(choices.CreditStatus.CANCELLED, user, note)
        return False

    def get_current_status_duration(self):
        """Get how long the credit has been in current status."""
        latest_history = self.status_history.first()
        if latest_history:
            return timezone.now() - latest_history.created
        return timezone.now() - self.created

    def get_status_date(self, status: str):
        """Get the date when the credit reached a specific status."""
        history = self.status_history.filter(status=status).first()
        return history.created.date() if history else None

    def get_possible_status_transitions(self, user=None):
        """Get list of possible status transitions based on current status and user permissions."""
        transitions = {
            choices.CreditStatus.PENDING: [
                choices.CreditStatus.APPROVED,
                choices.CreditStatus.REJECTED,
                choices.CreditStatus.CANCELLED,
            ],
            choices.CreditStatus.APPROVED: [
                choices.CreditStatus.CANCELLED,
            ],
            choices.CreditStatus.ACTIVE: [
                choices.CreditStatus.CANCELLED,
            ],
        }

        possible_statuses = transitions.get(self.status, [])

        # Filter by user permissions if user is provided
        if user and hasattr(user, "has_perm"):
            filtered_statuses = []
            for status in possible_statuses:
                if status == choices.CreditStatus.APPROVED:
                    if user.has_perm("credits.approve_credit"):
                        filtered_statuses.append(status)
                elif status == choices.CreditStatus.REJECTED:
                    if user.has_perm("credits.reject_credit"):
                        filtered_statuses.append(status)
                else:
                    filtered_statuses.append(status)
            possible_statuses = filtered_statuses

        return possible_statuses

    @property
    def total_interest(self) -> Decimal:
        """Calculate total interest for the credit."""
        if self.payment_amount and self.term_duration and self.payment_frequency:
            # Calculate total number of payments based on frequency
            payment_periods = {
                choices.PaymentFrequency.WEEKLY: 52,
                choices.PaymentFrequency.BIWEEKLY: 26,
                choices.PaymentFrequency.MONTHLY: 12,
                choices.PaymentFrequency.QUARTERLY: 4,
                choices.PaymentFrequency.ANNUALLY: 1,
            }
            periods_per_year = payment_periods.get(self.payment_frequency, 12)
            total_payments = (self.term_duration * periods_per_year) // 12

            return (self.payment_amount * total_payments) - self.amount
        return Decimal("0.00")

    @property
    def total_repayment(self) -> Decimal:
        """Calculate total repayment amount."""
        return self.amount + self.total_interest

    def get_current_installments(self):
        """
        Get the current installments for this credit based on current_version.

        Returns:
            QuerySet: Installments for the current schedule version ordered by due_date.
        """
        return self.installments.filter(schedule_version=self.current_version).order_by(
            "due_date"
        )

    def get_unpaid_installments(self):
        """
        Get unpaid installments for the current version.

        Returns:
            QuerySet: Unpaid installments (pending, overdue, or partial) for current version.
        """
        return self.installments.filter(
            schedule_version=self.current_version,
            status__in=[
                choices.InstallmentStatus.PENDING,
                choices.InstallmentStatus.OVERDUE,
                choices.InstallmentStatus.PARTIAL,
            ],
        )


class CreditApplication(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a credit application/request."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="credit_applications",
        help_text=_("Partner who is applying for the credit."),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="applications",
        help_text=_("Product this application is for."),
    )
    requested_amount = models.DecimalField(
        _("Requested Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount of credit requested."),
    )
    proposed_interest_rate = models.DecimalField(
        _("Proposed Interest Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text=_("Proposed annual interest rate percentage."),
    )
    requested_term_duration = models.PositiveIntegerField(
        _("Requested Term Duration"),
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text=_("Requested duration of the credit in months."),
    )
    requested_payment_frequency = models.CharField(
        _("Requested Payment Frequency"),
        max_length=15,
        choices=choices.PaymentFrequency.choices,
        null=True,
        blank=True,
        help_text=_(
            "Requested frequency for payments. If not specified, uses product default."
        ),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.CreditApplicationStatus.choices,
        default=choices.CreditApplicationStatus.DRAFT,
        help_text=_("Current status of the application."),
    )
    estimated_payment_amount = models.DecimalField(
        _("Estimated Payment Amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Estimated payment amount based on requested terms and frequency."),
    )
    payment_schedule = models.JSONField(
        _("Payment Schedule"),
        null=True,
        blank=True,
        help_text=_("JSON representation of the generated payment schedule."),
    )
    assigned_to = models.ForeignKey(
        "team.Employee",
        on_delete=models.SET_NULL,
        related_name="assigned_applications",
        null=True,
        blank=True,
        help_text=_("Employee assigned to review this application."),
    )
    possible_start_date = models.DateField(
        _("Possible Start Date"),
        null=True,
        blank=True,
        help_text=_("Estimated date when the credit could start."),
    )
    proposed_delinquency_rate = models.DecimalField(
        _("Proposed Delinquency Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        null=True,
        blank=True,
        help_text=_("Proposed delinquency rate percentage for overdue payments."),
    )

    # Generic relation to status history
    status_history = GenericRelation(
        "core.StatusHistory",
        help_text=_("History of status changes for this application."),
    )

    class Meta:
        verbose_name = _("Credit Application")
        verbose_name_plural = _("Credit Applications")
        ordering = ["-created"]
        permissions = [
            (
                "submit_creditapplication",
                "Can submit credit applications",
            ),
            (
                "review_creditapplication",
                "Can review credit applications",
            ),
            (
                "approve_creditapplication",
                "Can approve credit applications",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.partner.full_name} - {self.product.name} - ${self.requested_amount:,.2f}"

    def change_status(self, new_status: str, user, note: str = ""):
        """Change the status and create a history entry."""
        if self.status == new_status:
            return False

        # Store the previous status before changing it
        # For first status change, if no history exists and current status is DRAFT,
        # use DRAFT as the previous status
        previous_status = self.status

        # Update the current status
        self.status = new_status
        self.modified_by = user
        self.save()

        # Create status history entry
        core_models.StatusHistory.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            status=new_status,
            previous_status=previous_status,
            note=note,
            created_by=user,
            modified_by=user,
        )
        return True

    def submit(self, user=None, note: str = ""):
        """Submit the application for review."""
        if self.status == choices.CreditApplicationStatus.DRAFT:
            return self.change_status(
                choices.CreditApplicationStatus.SUBMITTED, user, note
            )
        return False

    def request_additional_info(self, user=None, note: str = ""):
        """Request additional information for the application."""
        if self.status in [
            choices.CreditApplicationStatus.SUBMITTED,
            choices.CreditApplicationStatus.UNDER_REVIEW,
        ]:
            return self.change_status(
                choices.CreditApplicationStatus.ADDITIONAL_INFO, user, note
            )
        return False

    def start_review(self, user=None, note: str = ""):
        """Start the review process for the application."""
        if self.status == choices.CreditApplicationStatus.SUBMITTED:
            return self.change_status(
                choices.CreditApplicationStatus.UNDER_REVIEW, user, note
            )
        return False

    def approve(self, user=None, note: str = ""):
        """Approve the application."""
        if self.status in [
            choices.CreditApplicationStatus.SUBMITTED,
            choices.CreditApplicationStatus.UNDER_REVIEW,
        ]:
            return self.change_status(
                choices.CreditApplicationStatus.APPROVED, user, note
            )
        return False

    def reject(self, user=None, note: str = ""):
        """Reject the application with a reason."""
        if self.status in [
            choices.CreditApplicationStatus.SUBMITTED,
            choices.CreditApplicationStatus.UNDER_REVIEW,
        ]:
            return self.change_status(
                choices.CreditApplicationStatus.REJECTED, user, note
            )
        return False

    def cancel(self, user=None, note: str = ""):
        """Cancel the application."""
        if self.status not in [
            choices.CreditApplicationStatus.APPROVED,
            choices.CreditApplicationStatus.REJECTED,
        ]:
            return self.change_status(
                choices.CreditApplicationStatus.CANCELLED, user, note
            )
        return False

    def get_current_status_duration(self):
        """Get how long the application has been in current status."""
        latest_history = self.status_history.first()
        if latest_history:
            return timezone.now() - latest_history.created
        return timezone.now() - self.created

    def get_status_date(self, status: str):
        """Get the date when the application reached a specific status."""
        history = self.status_history.filter(status=status).first()
        return history.created.date() if history else None

    @property
    def submission_date(self):
        """Get submission date from status history."""
        return self.get_status_date(choices.CreditApplicationStatus.SUBMITTED)

    @property
    def review_date(self):
        """Get review date from status history."""
        return self.get_status_date(choices.CreditApplicationStatus.UNDER_REVIEW)

    @property
    def decision_date(self):
        """Get decision date from status history."""
        approved_date = self.get_status_date(choices.CreditApplicationStatus.APPROVED)
        rejected_date = self.get_status_date(choices.CreditApplicationStatus.REJECTED)
        # Return the earliest decision date
        if approved_date and rejected_date:
            return min(approved_date, rejected_date)
        return approved_date or rejected_date

    @property
    def rejection_reason(self):
        """Get rejection reason from status history."""
        rejected_history = self.status_history.filter(
            status=choices.CreditApplicationStatus.REJECTED
        ).first()
        return rejected_history.note if rejected_history else ""

    def get_possible_status_transitions(self, user=None):
        """Get list of possible status transitions based on current status and user permissions."""
        transitions = {
            choices.CreditApplicationStatus.DRAFT: [
                choices.CreditApplicationStatus.SUBMITTED,
                choices.CreditApplicationStatus.CANCELLED,
            ],
            choices.CreditApplicationStatus.SUBMITTED: [
                choices.CreditApplicationStatus.UNDER_REVIEW,
                choices.CreditApplicationStatus.ADDITIONAL_INFO,
                choices.CreditApplicationStatus.APPROVED,
                choices.CreditApplicationStatus.REJECTED,
                choices.CreditApplicationStatus.CANCELLED,
            ],
            choices.CreditApplicationStatus.UNDER_REVIEW: [
                choices.CreditApplicationStatus.ADDITIONAL_INFO,
                choices.CreditApplicationStatus.APPROVED,
                choices.CreditApplicationStatus.REJECTED,
            ],
            choices.CreditApplicationStatus.ADDITIONAL_INFO: [
                choices.CreditApplicationStatus.SUBMITTED,
                choices.CreditApplicationStatus.CANCELLED,
            ],
        }

        possible_statuses = transitions.get(self.status, [])

        # Filter by user permissions if user is provided
        if user and hasattr(user, "has_perm"):
            filtered_statuses = []
            for status in possible_statuses:
                if status in [
                    choices.CreditApplicationStatus.APPROVED,
                    choices.CreditApplicationStatus.REJECTED,
                ]:
                    if user.has_perm("credits.approve_creditapplication"):
                        filtered_statuses.append(status)
                elif status == choices.CreditApplicationStatus.UNDER_REVIEW:
                    if user.has_perm("credits.review_creditapplication"):
                        filtered_statuses.append(status)
                else:
                    filtered_statuses.append(status)
            possible_statuses = filtered_statuses

        return possible_statuses

    def generate_payment_schedule(self, start_date=None):
        """
        Generate a payment schedule based on application terms and store it in the payment_schedule field.

        This method calculates amortization schedule using the French method (fixed payments).
        It creates a detailed payment plan with dates, amounts, and balances that can be used
        for both estimation purposes and later for creating actual installments if approved.

        Args:
            start_date: Optional start date for the schedule. If not provided, uses current date.

        Returns:
            bool: True if the schedule was generated successfully, False otherwise.
        """
        # Use requested terms
        amount = self.requested_amount
        interest_rate = self.proposed_interest_rate
        term_duration = self.requested_term_duration

        if not amount or not interest_rate or not term_duration:
            return False

        # Determine payment frequency and number of payments
        # Use requested frequency, then product default
        payment_frequency = (
            self.requested_payment_frequency or self.product.payment_frequency
        )
        payment_periods = {
            choices.PaymentFrequency.WEEKLY: 52,
            choices.PaymentFrequency.BIWEEKLY: 26,
            choices.PaymentFrequency.MONTHLY: 12,
            choices.PaymentFrequency.QUARTERLY: 4,
            choices.PaymentFrequency.ANNUALLY: 1,
        }

        periods_per_year = payment_periods.get(
            payment_frequency, 12
        )  # Default to monthly
        total_periods = (term_duration * periods_per_year) // 12

        # Calculate period interest rate
        annual_rate = interest_rate / Decimal("100")
        period_rate = annual_rate / periods_per_year

        # Calculate fixed payment amount using formula: PMT = P * r * (1+r)^n / ((1+r)^n - 1)
        if period_rate == 0:
            payment_amount = amount / total_periods
        else:
            payment_amount = amount * period_rate * (1 + period_rate) ** total_periods
            payment_amount = payment_amount / ((1 + period_rate) ** total_periods - 1)
            payment_amount = payment_amount.quantize(
                Decimal("0.01"), rounding="ROUND_HALF_UP"
            )

        # Store the estimated payment amount based on frequency
        self.estimated_payment_amount = payment_amount

        # Create payment schedule
        schedule = []
        remaining_balance = amount
        if start_date is None:
            start_date = timezone.now().date()

        # Determine days between payments based on frequency
        days_between_payments = {
            choices.PaymentFrequency.WEEKLY: 7,
            choices.PaymentFrequency.BIWEEKLY: 14,
            choices.PaymentFrequency.MONTHLY: 30,  # Simplified; actual implementation might use month increment
            choices.PaymentFrequency.QUARTERLY: 90,
            choices.PaymentFrequency.ANNUALLY: 365,
        }
        days_interval = days_between_payments.get(payment_frequency, 30)

        for period in range(1, total_periods + 1):
            # Calculate payment date
            if payment_frequency == choices.PaymentFrequency.MONTHLY:
                # For monthly payments, increment by actual months
                payment_date = utils.add_months(start_date, period)
            else:
                # For other frequencies, add days
                payment_date = start_date + timezone.timedelta(
                    days=period * days_interval
                )

            # Calculate interest and principal for this period
            interest_payment = remaining_balance * period_rate
            interest_payment = interest_payment.quantize(
                Decimal("0.01"), rounding="ROUND_HALF_UP"
            )

            # Last payment might need adjustment to ensure exact payoff
            if period == total_periods:
                principal_payment = remaining_balance
                payment_amount = principal_payment + interest_payment
            else:
                principal_payment = payment_amount - interest_payment

            # Update remaining balance
            remaining_balance -= principal_payment
            if remaining_balance < Decimal("0.01"):
                remaining_balance = Decimal("0")

            # Add payment to schedule
            schedule.append(
                {
                    "period": period,
                    "payment_date": payment_date.isoformat(),
                    "payment_amount": float(payment_amount),
                    "principal": float(principal_payment),
                    "interest": float(interest_payment),
                    "remaining_balance": float(remaining_balance),
                }
            )

        # Store schedule in payment_schedule field
        self.payment_schedule = {
            "credit_amount": float(amount),
            "interest_rate": float(interest_rate),
            "term_duration": term_duration,
            "payment_frequency": payment_frequency,
            "payment_amount": float(payment_amount),
            "total_payments": total_periods,
            "first_payment_date": start_date.isoformat(),
            "schedule": schedule,
        }

        # Save the updated application object
        self.save(update_fields=["payment_schedule", "estimated_payment_amount"])

        return True

    def create_credit(self):
        """
        Create a credit from this approved application.

        This method creates a credit based on the approved application and also
        creates the installments based on the payment schedule if available.

        Returns:
            Credit: The created credit object or None if creation failed.
        """
        from apps.credits import utils

        if self.status != choices.CreditApplicationStatus.APPROVED:
            return None

        # Generate payment schedule if not already generated
        if not self.payment_schedule:
            self.generate_payment_schedule()

        # Use the utility function to create the credit
        return utils.create_credit_with_installments(
            partner=self.partner,
            product=self.product,
            amount=self.requested_amount,
            interest_rate=self.proposed_interest_rate,
            term_duration=self.requested_term_duration,
            payment_frequency=self.requested_payment_frequency
            or self.product.payment_frequency,
            start_date=self.possible_start_date or timezone.now().date(),
            delinquency_rate=self.proposed_delinquency_rate,
            status=choices.CreditStatus.PENDING,
            application_date=self.submission_date or self.created.date(),
            approval_date=self.decision_date,
            notes="",
            created_by=self.modified_by or self.created_by,
            application=self,
            payment_schedule=self.payment_schedule,
        )


class Installment(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent an installment in the loan amortization schedule."""

    credit = models.ForeignKey(
        Credit,
        on_delete=models.CASCADE,
        related_name="installments",
        help_text=_("Credit this installment belongs to."),
    )
    installment_number = models.PositiveIntegerField(
        _("Installment Number"),
        help_text=_("Sequential installment number in the amortization schedule."),
    )
    due_date = models.DateField(
        _("Due Date"),
        help_text=_("Date when this installment is due."),
    )
    installment_amount = models.DecimalField(
        _("Installment Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Total installment amount (principal + interest)."),
    )
    principal_amount = models.DecimalField(
        _("Principal Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Principal portion of the installment."),
    )
    interest_amount = models.DecimalField(
        _("Interest Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Interest portion of the installment."),
    )
    balance_after = models.DecimalField(
        _("Balance After Payment"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Outstanding balance after this installment is paid."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.InstallmentStatus.choices,
        default=choices.InstallmentStatus.PENDING,
        help_text=_("Current status of the installment."),
    )
    payment_date = models.DateField(
        _("Payment Date"),
        null=True,
        blank=True,
        help_text=_("Date when this installment was actually paid."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about this installment."),
    )
    payment_allocations = GenericRelation(
        "payments.PaymentConceptAllocation",
        help_text=_("Payment allocations for this installment."),
    )
    schedule_version = models.PositiveIntegerField(
        _("Schedule Version"),
        default=1,
        help_text=_("Version of the payment schedule this installment belongs to."),
    )

    class Meta:
        verbose_name = _("Installment")
        verbose_name_plural = _("Installments")
        ordering = ["credit", "installment_number"]
        unique_together = ["credit", "schedule_version", "installment_number"]

    def __str__(self) -> str:
        return f"Installment #{self.installment_number} - {self.credit.partner.full_name} - ${self.installment_amount:,.2f}"

    @property
    def is_paid(self) -> bool:
        """Check if installment is fully paid."""
        return self.status == choices.InstallmentStatus.PAID

    @property
    def is_overdue(self) -> bool:
        """Check if installment is overdue."""
        return (
            self.id
            and self.status
            in [
                choices.InstallmentStatus.PENDING,
                choices.InstallmentStatus.PARTIAL,
                choices.InstallmentStatus.OVERDUE,
            ]
            and self.due_date <= timezone.now().date()
        )

    @property
    def days_overdue(self) -> int:
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def amount_paid(self) -> Decimal:
        """Calculate total amount paid towards this installment."""
        return sum(
            allocation.amount_applied
            for allocation in self.payment_allocations.filter(
                payment__status=payment_choices.PaymentStatus.PAID
            )
        )

    @property
    def remaining_balance(self) -> Decimal:
        """Calculate remaining balance for this installment."""
        return self.installment_amount - self.amount_paid


class CreditRescheduleRequest(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a credit reschedule request."""

    credit = models.ForeignKey(
        Credit,
        on_delete=models.CASCADE,
        related_name="reschedule_requests",
        help_text=_("Credit this reschedule request is for."),
    )
    requested_term_extension = models.PositiveIntegerField(
        _("Requested Term Extension (months)"),
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text=_("Number of months to extend the loan term."),
    )
    requested_interest_rate_adjustment = models.DecimalField(
        _("Requested Interest Rate Adjustment (%)"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("-5.00")),
            MaxValueValidator(Decimal("5.00")),
        ],
        help_text=_("Percentage adjustment to the interest rate."),
    )
    reason = models.TextField(
        _("Reason for Reschedule"),
        help_text=_("Reason for requesting the loan reschedule."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.RescheduleRequestStatus.choices,
        default=choices.RescheduleRequestStatus.PENDING,
        help_text=_("Current status of the reschedule request."),
    )
    request_date = models.DateField(
        _("Request Date"),
        auto_now_add=True,
        help_text=_("Date when the reschedule request was made."),
    )
    review_date = models.DateField(
        _("Review Date"),
        null=True,
        blank=True,
        help_text=_("Date when the reschedule request was reviewed."),
    )
    decision_date = models.DateField(
        _("Decision Date"),
        null=True,
        blank=True,
        help_text=_("Date when decision was made on the reschedule request."),
    )
    requested_start_date = models.DateField(
        _("Requested Start Date"),
        null=True,
        blank=True,
        help_text=_("Requested start date for the rescheduled credit installments."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about the reschedule request."),
    )

    class Meta:
        verbose_name = _("Credit Reschedule Request")
        verbose_name_plural = _("Credit Reschedule Requests")
        ordering = ["-created"]
        permissions = [
            (
                "view_credit_summary",
                "Can view credit summary information",
            ),
            (
                "submit_creditreschedule",
                "Can submit credit reschedule requests",
            ),
            (
                "review_creditreschedule",
                "Can review credit reschedule requests",
            ),
            (
                "approve_creditreschedule",
                "Can approve credit reschedule requests",
            ),
        ]

    def __str__(self) -> str:
        return f"Reschedule Request for {self.credit.partner.full_name} - {self.credit.product.name}"


class CreditRefinanceRequest(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a credit refinancing request."""

    credit = models.ForeignKey(
        Credit,
        on_delete=models.CASCADE,
        related_name="refinance_requests",
        help_text=_("Credit being refinanced."),
    )
    resulting_credit = models.OneToOneField(
        Credit,
        on_delete=models.SET_NULL,
        related_name="refinanced_from",
        null=True,
        blank=True,
        help_text=_("New credit created as a result of this refinancing."),
    )

    # Términos anteriores
    previous_outstanding_balance = models.DecimalField(
        _("Previous Outstanding Balance"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Outstanding balance before rescheduling."),
    )
    previous_term_remaining = models.PositiveIntegerField(
        _("Previous Term Remaining (months)"),
        help_text=_("Remaining months before rescheduling."),
    )

    # Nuevos términos
    new_payment_frequency = models.CharField(
        _("New Payment Frequency"),
        max_length=15,
        choices=choices.PaymentFrequency.choices,
        default=choices.PaymentFrequency.MONTHLY,
        help_text=_("New payment frequency."),
    )
    new_term_duration = models.PositiveIntegerField(
        _("New Term Duration (months)"),
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text=_("New total duration in months."),
    )
    new_interest_rate = models.DecimalField(
        _("New Interest Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text=_("New interest rate percentage."),
    )
    new_delinquency_rate = models.DecimalField(
        _("New Delinquency Rate"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        default=Decimal("0.00"),
        help_text=_("New delinquency rate percentage for overdue payments."),
    )

    # Información financiera
    additional_amount = models.DecimalField(
        _("Additional Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Any additional amount added to the outstanding balance."),
    )

    start_date = models.DateField(
        _("Start Date"),
        help_text=_("Start date for new installments."),
    )
    reason = models.TextField(
        _("Reason"),
        help_text=_("Reason for the rescheduling."),
    )

    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.RefinanceRequestStatus.choices,
        default=choices.RefinanceRequestStatus.PENDING,
        help_text=_("Current status of the refinance request."),
    )

    class Meta:
        verbose_name = _("Credit Refinance Request")
        verbose_name_plural = _("Credit Refinance Requests")
        ordering = ["-created"]

    def __str__(self):
        return f"Refinance Request for {self.credit.partner.full_name} - {self.credit.product.name}"


class CreditDisbursement(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a credit disbursement."""

    credit = models.ForeignKey(
        Credit,
        on_delete=models.PROTECT,
        related_name="disbursements",
        help_text=_("Credit being disbursed."),
    )
    disbursement_amount = models.DecimalField(
        _("Disbursement Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount to be disbursed."),
    )
    scheduled_date = models.DateField(
        _("Scheduled Date"),
        help_text=_("Date when the disbursement is scheduled."),
    )
    disbursement_method = models.CharField(
        _("Disbursement Method"),
        max_length=20,
        choices=choices.DisbursementMethod.choices,
        default=choices.DisbursementMethod.BANK_TRANSFER,
        help_text=_("Method used for disbursement."),
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=choices.DisbursementStatus.choices,
        default=choices.DisbursementStatus.PENDING,
        help_text=_("Current status of the disbursement."),
    )

    # Bank transfer details
    bank_name = models.CharField(
        _("Bank Name"),
        max_length=100,
        blank=True,
        help_text=_("Name of the bank for transfer."),
    )
    account_number = models.CharField(
        _("Account Number"),
        max_length=50,
        blank=True,
        help_text=_("Account number for transfer."),
    )
    account_holder_name = models.CharField(
        _("Account Holder Name"),
        max_length=200,
        blank=True,
        help_text=_("Name of the account holder."),
    )

    # Check details
    check_number = models.CharField(
        _("Check Number"),
        max_length=50,
        blank=True,
        help_text=_("Check number if disbursement method is check."),
    )

    # Reference information
    reference_number = models.CharField(
        _("Reference Number"),
        max_length=100,
        blank=True,
        help_text=_("Transaction reference number."),
    )
    receipt_document = models.FileField(
        _("Receipt Document"),
        upload_to="disbursements/receipts/%Y/%m/",
        null=True,
        blank=True,
        help_text=_("Upload receipt or proof of disbursement."),
    )

    # Generic relation to status history
    status_history = GenericRelation(
        "core.StatusHistory",
        help_text=_("History of status changes for this disbursement."),
    )

    class Meta:
        verbose_name = _("Credit Disbursement")
        verbose_name_plural = _("Credit Disbursements")
        ordering = ["-scheduled_date", "-created"]
        permissions = [
            ("approve_creditdisbursement", "Can approve credit disbursements"),
            ("process_creditdisbursement", "Can process credit disbursements"),
        ]

    def __str__(self) -> str:
        return f"Disbursement for {self.credit.partner.full_name} - ${self.disbursement_amount:,.2f} - {self.get_status_display()}"

    def change_status(self, new_status: str, user, note: str = ""):
        """
        Change the disbursement status and create a history entry.

        Args:
            new_status: The new status to set.
            user: The user making the change.
            note: Optional note about the status change.

        Returns:
            bool: True if status was changed, False otherwise.
        """
        if self.status == new_status:
            return False

        previous_status = self.status
        self.status = new_status
        self.modified_by = user
        self.save()

        # Create status history entry
        core_models.StatusHistory.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            status=new_status,
            previous_status=previous_status,
            note=note,
            created_by=user,
            modified_by=user,
        )
        return True

    def get_status_date(self, status: str):
        """
        Get the date when the disbursement reached a specific status.

        Args:
            status: The status to search for.

        Returns:
            date: The date when the status was reached, or None.
        """
        history = self.status_history.filter(status=status).first()
        return history.created.date() if history else None
