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


class IntentType(models.TextChoices):
    """Intent types for user messages."""

    GREETING = "GREETING", _("Greeting")
    AUTHENTICATION = "AUTHENTICATION", _("Authentication")
    PARTNER_DETAIL = "PARTNER_DETAIL", _("Partner Detail")
    ACCOUNT_STATEMENT = "ACCOUNT_STATEMENT", _("Account Statement")
    LIST_CREDITS = "LIST_CREDITS", _("List Credits")
    CREDIT_DETAIL = "CREDIT_DETAIL", _("Credit Detail")
    CREATE_TICKET = "CREATE_TICKET", _("Create Support Ticket")
    UPLOAD_RECEIPT = "UPLOAD_RECEIPT", _("Upload Payment Receipt")
    HELP = "HELP", _("Help")
    GOODBYE = "GOODBYE", _("Goodbye")
    UNKNOWN = "UNKNOWN", _("Unknown")


class ChannelType(models.TextChoices):
    """Channel types for conversations."""

    TELEGRAM = "TELEGRAM", _("Telegram")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
