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


class NotificationType(models.TextChoices):
    """Types of campaign notifications."""

    BEFORE_3_DAYS = "BEFORE_3_DAYS", _("3 Days Before Due Date")
    ON_DUE_DATE = "ON_DUE_DATE", _("On Due Date")
    AFTER_3_DAYS = "AFTER_3_DAYS", _("3 Days After Due Date")
    AFTER_7_DAYS = "AFTER_7_DAYS", _("7 Days After Due Date")


class NotificationStatus(models.TextChoices):
    """Status of campaign notifications."""

    PENDING = "PENDING", _("Pending")
    SENT = "SENT", _("Sent")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class NotificationChannel(models.TextChoices):
    """Channels for campaign notifications."""

    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    PHONE_CALL = "PHONE_CALL", _("Phone Call")
