from django.db import models
from django.utils.translation import gettext_lazy as _


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

    TELEGRAM = "TELEGRAM", _("Telegram")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    SMS = "SMS", _("SMS")
    EMAIL = "EMAIL", _("Email")
