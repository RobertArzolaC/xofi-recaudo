from django.db import models
from django.utils.translation import gettext_lazy as _


class CampaignStatus(models.TextChoices):
    """Status choices for campaigns."""

    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    PAUSED = "PAUSED", _("Paused")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class GroupPriority(models.IntegerChoices):
    """Priority levels for groups."""

    LOW = 1, _("Low")
    MEDIUM = 2, _("Medium")
    HIGH = 3, _("High")
    URGENT = 4, _("Urgent")
