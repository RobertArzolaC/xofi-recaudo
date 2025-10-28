from django.db import models
from django.utils.translation import gettext_lazy as _


class ApplicantStatus(models.IntegerChoices):
    PENDING = 0, _("Pending")
    VALIDATING = 1, _("Validating")
    APPROVED = 2, _("Approved")
    REJECTED = 3, _("Rejected")


class PartnerStatus(models.IntegerChoices):
    PENDING = 0, _("Pending")
    ACTIVE = 1, _("Active")
    INACTIVE = 2, _("Inactive")
    SUSPENDED = 3, _("Suspended")
    EXPELLED = 4, _("Expelled")
    DECEASED = 5, _("Deceased")


class EmploymentType(models.IntegerChoices):
    """Employment types according to Peruvian labor regulations."""

    DEPENDENT = 0, _("Dependent Employee")
    INDEPENDENT = 1, _("Independent Worker")
    SERVICES = 2, _("Services Provider")
    CONSULTANT = 3, _("Consultant")
    COMMISSION = 4, _("Commission Agent")


class ContractType(models.IntegerChoices):
    """Contract types according to Peruvian labor law."""

    INDEFINITE = 0, _("Indefinite Term")
    FIXED_TERM = 1, _("Fixed Term")
    PART_TIME = 2, _("Part Time")
    TEMPORAL = 3, _("Temporary")
    SEASONAL = 4, _("Seasonal")
    TRAINING = 5, _("Training/Apprenticeship")
    SERVICES = 6, _("Services Contract")
    OUTSOURCING = 7, _("Outsourcing")


class WorkScheduleType(models.IntegerChoices):
    """Work schedule types."""

    FULL_TIME = 0, _("Full Time")
    PART_TIME = 1, _("Part Time")
    FLEXIBLE = 2, _("Flexible")
    SHIFT_WORK = 3, _("Shift Work")
    REMOTE = 4, _("Remote Work")
    HYBRID = 5, _("Hybrid")


class EducationLevel(models.IntegerChoices):
    """Education levels."""

    PRIMARY = 0, _("Primary Education")
    SECONDARY = 1, _("Secondary Education")
    TECHNICAL = 2, _("Technical Education")
    UNIVERSITY = 3, _("University Education")
    POSTGRADUATE = 4, _("Postgraduate")
    DOCTORATE = 5, _("Doctorate")


class SalaryFrequency(models.IntegerChoices):
    """Salary payment frequency."""

    DAILY = 0, _("Daily")
    WEEKLY = 1, _("Weekly")
    BIWEEKLY = 2, _("Biweekly")
    MONTHLY = 3, _("Monthly")
    ANNUAL = 4, _("Annual")


class ProspectStatus(models.IntegerChoices):
    """Status choices for prospects."""

    NEW = 0, _("New")
    CONTACTED = 1, _("Contacted")
    INTERESTED = 2, _("Interested")
    QUALIFIED = 3, _("Qualified")
    CONVERTED = 4, _("Converted to Partner")
    REJECTED = 5, _("Rejected")
    LOST = 6, _("Lost")
