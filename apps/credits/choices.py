from django.db import models
from django.utils.translation import gettext_lazy as _


class CreditStatus(models.TextChoices):
    """Choices for credit status."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    DEFAULTED = "DEFAULTED", _("Defaulted")
    CANCELLED = "CANCELLED", _("Cancelled")
    RESCHEDULED = "RESCHEDULED", _("Rescheduled")
    REFINANCED = "REFINANCED", _("Refinanced")


class CreditApplicationStatus(models.TextChoices):
    """Choices for credit application status."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    ADDITIONAL_INFO = "ADDITIONAL_INFO", _("Additional Information Required")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class InterestType(models.TextChoices):
    """Choices for interest type."""

    FIXED = "FIXED", _("Fixed")
    VARIABLE = "VARIABLE", _("Variable")


class PaymentFrequency(models.TextChoices):
    """Choices for payment frequency."""

    WEEKLY = "WEEKLY", _("Weekly")
    BIWEEKLY = "BIWEEKLY", _("Biweekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    ANNUALLY = "ANNUALLY", _("Annually")


class InstallmentStatus(models.TextChoices):
    """Choices for installment status."""

    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    OVERDUE = "OVERDUE", _("Overdue")
    PARTIAL = "PARTIAL", _("Partial")
    CANCELLED = "CANCELLED", _("Cancelled")
    RESCHEDULED = "RESCHEDULED", _("Rescheduled")
    REFINANCED = "REFINANCED", _("Refinanced")


class RescheduleRequestStatus(models.TextChoices):
    """Choices for reschedule request status."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class RefinanceRequestStatus(models.TextChoices):
    """Choices for refinance request status."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class DisbursementStatus(models.TextChoices):
    """Choices for disbursement status."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    PROCESSING = "PROCESSING", _("Processing")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class DisbursementMethod(models.TextChoices):
    """Choices for disbursement method."""

    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    CHECK = "CHECK", _("Check")
    CASH = "CASH", _("Cash")
    ELECTRONIC_WALLET = "ELECTRONIC_WALLET", _("Electronic Wallet")
    OTHER = "OTHER", _("Other")
