from django.db import models
from django.utils.translation import gettext_lazy as _


class ComplianceStatus(models.TextChoices):
    """Universal status for all compliance-related records."""

    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    OVERDUE = "OVERDUE", _("Overdue")
    PARTIAL = "PARTIAL", _("Partial Payment")
    WAIVED = "WAIVED", _("Waived")
    APPEALED = "APPEALED", _("Under Appeal")
    CANCELLED = "CANCELLED", _("Cancelled")


class ContributionType(models.TextChoices):
    """Types of contributions."""

    HEALTH = "HEALTH", _("Health Insurance")
    PENSION = "PENSION", _("Pension")
    UNEMPLOYMENT = "UNEMPLOYMENT", _("Unemployment Insurance")
    WORKERS_COMP = "WORKERS_COMP", _("Workers Compensation")
    DISABILITY = "DISABILITY", _("Disability Insurance")
    FAMILY_ALLOWANCE = "FAMILY_ALLOWANCE", _("Family Allowance")


class ContributionPeriod(models.TextChoices):
    """Contribution calculation periods."""

    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    ANNUALLY = "ANNUALLY", _("Annually")


class PenaltyType(models.TextChoices):
    """Types of penalties."""

    LATE_PAYMENT = "LATE_PAYMENT", _("Late Payment")
    INCORRECT_DECLARATION = "INCORRECT_DECLARATION", _("Incorrect Declaration")
    MISSING_DECLARATION = "MISSING_DECLARATION", _("Missing Declaration")
    ADMINISTRATIVE = "ADMINISTRATIVE", _("Administrative Penalty")
    TAX_VIOLATION = "TAX_VIOLATION", _("Tax Violation")
