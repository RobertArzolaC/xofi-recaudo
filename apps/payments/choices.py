from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentStatus(models.TextChoices):
    """Choices for payment status."""

    PAID = "PAID", _("Paid")
    CANCELLED = "CANCELLED", _("Cancelled")
    REFUNDED = "REFUNDED", _("Refunded")


class PaymentMethod(models.TextChoices):
    """Choices for payment method."""

    CASH = "CASH", _("Cash")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    CHECK = "CHECK", _("Check")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    DEBIT_CARD = "DEBIT_CARD", _("Debit Card")
    ELECTRONIC_WALLET = "ELECTRONIC_WALLET", _("Electronic Wallet")
    CULQI_ONLINE = "CULQI_ONLINE", _("Online Payment (Culqi)")
    OTHER = "OTHER", _("Other")


class AllocationStatus(models.TextChoices):
    """Choices for payment allocation status."""

    FULL = "FULL", _("Full Payment")
    PARTIAL = "PARTIAL", _("Partial Payment")
    OVERPAYMENT = "OVERPAYMENT", _("Overpayment")


class PaymentConcept(models.TextChoices):
    """Choices for different payment concepts."""

    INSTALLMENT = "INSTALLMENT", _("Installment")
    CONTRIBUTION = "CONTRIBUTION", _("Contribution")
    SOCIAL_SECURITY = "SOCIAL_SECURITY", _("Social Security")
    PENALTY = "PENALTY", _("Penalty")


class ReceiptStatus(models.TextChoices):
    """Choices for payment receipt validation status."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class MagicLinkStatus(models.TextChoices):
    """Choices for magic payment link status."""

    ACTIVE = "ACTIVE", _("Active")
    USED = "USED", _("Used")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")


class MagicLinkSource(models.TextChoices):
    """Choices for magic payment link source."""

    MANUAL = "MANUAL", _("Manual")
    AUTOMATED = "AUTOMATED", _("Automated")
