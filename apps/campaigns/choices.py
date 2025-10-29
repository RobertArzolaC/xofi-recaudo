from django.db import models
from django.utils.translation import gettext_lazy as _


class CampaignStatus(models.TextChoices):
    """Status choices for campaigns."""

    DRAFT = "DRAFT", _("Draft")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    PROCESSING = "PROCESSING", _("Processing")
    SENDING = "SENDING", _("Sending")
    ACTIVE = "ACTIVE", _("Active")
    PAUSED = "PAUSED", _("Paused")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class GroupPriority(models.IntegerChoices):
    """Priority levels for groups."""

    LOW = 1, _("Low")
    MEDIUM = 2, _("Medium")
    HIGH = 3, _("High")
    URGENT = 4, _("Urgent")


class NotificationType(models.TextChoices):
    """Types of campaign notifications."""

    SCHEDULED = "SCHEDULED", _("Scheduled Notification")


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
