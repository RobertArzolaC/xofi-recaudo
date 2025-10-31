from django.db import models
from django.utils.translation import gettext_lazy as _


class TicketPriority(models.IntegerChoices):
    """Ticket priority choices."""

    LOW = 1, _("Low")
    MEDIUM = 2, _("Medium")
    HIGH = 3, _("High")
    URGENT = 4, _("Urgent")


class TicketStatus(models.IntegerChoices):
    """Ticket status choices."""

    OPEN = 1, _("Open")
    IN_PROGRESS = 2, _("In Progress")
    WAITING_CUSTOMER = 3, _("Waiting for Customer")
    RESOLVED = 4, _("Resolved")
    CLOSED = 5, _("Closed")
