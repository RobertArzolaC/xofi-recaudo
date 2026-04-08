from django.db import models
from django.utils.translation import gettext_lazy as _


class ConversationStatus(models.IntegerChoices):
    """Status choices for conversations."""

    PENDING_AUTH = 1, _("Pending Authentication")
    AUTHENTICATED = 2, _("Authenticated")
    ACTIVE = 3, _("Active")
    CLOSED = 4, _("Closed")
    BLOCKED = 5, _("Blocked")


class MessageSender(models.TextChoices):
    """Sender type for conversation messages."""

    USER = "USER", _("User")
    AGENT = "AGENT", _("Agent")
    SYSTEM = "SYSTEM", _("System")



class ChannelType(models.TextChoices):
    """Channel types for conversations."""

    TELEGRAM = "TELEGRAM", _("Telegram")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    WEB = "WEB", _("Web (Testing)")


class MessageDeliveryStatus(models.TextChoices):
    """Delivery status for outbound WhatsApp messages."""

    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    READ = "READ", _("Read")
    FAILED = "FAILED", _("Failed")


class TemplateStatus(models.TextChoices):
    """Approval status for WhatsApp message templates."""

    PENDING = "PENDING", _("Pending Review")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    PAUSED = "PAUSED", _("Paused")
