from django.db import models
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.support import choices
from apps.team import choices as team_choices
from apps.team import models as team_models


class Ticket(core_models.BaseUserTracked, TimeStampedModel):
    """Support ticket model."""

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name=_("Partner"),
        help_text=_("Partner who created the ticket"),
    )

    assigned_to = models.ForeignKey(
        "team.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name=_("Assigned to"),
        help_text=_("Employee assigned to handle this ticket"),
    )

    subject = models.CharField(
        max_length=255,
        verbose_name=_("Subject"),
        help_text=_("Brief description of the issue"),
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the issue"),
    )

    priority = models.IntegerField(
        choices=choices.TicketPriority.choices,
        default=choices.TicketPriority.MEDIUM,
        verbose_name=_("Priority"),
    )

    status = models.IntegerField(
        choices=choices.TicketStatus.choices,
        default=choices.TicketStatus.OPEN,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status", "-created"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["partner", "-created"]),
        ]

    def __str__(self):
        return f"#{self.pk} - {self.subject}"

    @property
    def is_open(self):
        """Check if ticket is open."""
        return self.status in [
            choices.TicketStatus.OPEN,
            choices.TicketStatus.IN_PROGRESS,
            choices.TicketStatus.WAITING_CUSTOMER,
        ]

    @staticmethod
    def get_available_employee(agency=None):
        """
        Get the employee with the least workload for ticket assignment.

        Args:
            agency: Optional agency to filter employees by

        Returns:
            Employee instance or None
        """

        # Build base queryset for active employees
        queryset = team_models.Employee.objects.filter(
            status=team_choices.EmployeeStatus.ACTIVE
        )

        # Filter by agency if provided
        if agency:
            queryset = queryset.filter(agency=agency)

        # Annotate with open tickets count and get employee with minimum workload
        employee = (
            queryset.annotate(
                open_tickets=Count(
                    "assigned_tickets",
                    filter=Q(
                        assigned_tickets__status__in=[
                            choices.TicketStatus.OPEN,
                            choices.TicketStatus.IN_PROGRESS,
                            choices.TicketStatus.WAITING_CUSTOMER,
                        ]
                    ),
                )
            )
            .order_by("open_tickets")
            .first()
        )

        return employee

    def auto_assign(self):
        """Automatically assign ticket to available employee."""
        # Check if partner has an agency
        agency = self.partner.agency if self.partner else None

        # Get available employee
        employee = self.get_available_employee(agency=agency)

        if employee:
            self.assigned_to = employee
            self.save(update_fields=["assigned_to", "modified"])
            return True

        return False

    def save(self, *args, **kwargs):
        """Override save to auto-assign on creation."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Auto-assign if new ticket and not already assigned
        if is_new and not self.assigned_to:
            self.auto_assign()


class TicketComment(core_models.BaseUserTracked, TimeStampedModel):
    """Comment on a support ticket."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Ticket"),
    )

    comment = models.TextField(
        verbose_name=_("Comment"), help_text=_("Comment content")
    )

    is_internal = models.BooleanField(
        default=False,
        verbose_name=_("Internal Note"),
        help_text=_("Internal notes are only visible to employees"),
    )

    class Meta:
        verbose_name = _("Ticket Comment")
        verbose_name_plural = _("Ticket Comments")
        ordering = ["created"]
        indexes = [
            models.Index(fields=["ticket", "created"]),
        ]

    def __str__(self):
        return f"Comment on {self.ticket} by {self.created_by}"
