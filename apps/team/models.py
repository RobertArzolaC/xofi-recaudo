from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.team import choices


class Area(
    core_models.BaseUserTracked, core_models.NameDescription, TimeStampedModel
):
    """Model to represent an area within the organization."""

    class Meta:
        managed = False
        verbose_name = _("Area")
        verbose_name_plural = _("Areas")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Position(
    core_models.BaseUserTracked, core_models.NameDescription, TimeStampedModel
):
    """Model to represent a position within an area."""

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name="positions",
        help_text=_("Area this position belongs to."),
    )

    class Meta:
        managed = False
        ordering = ["area", "name"]
        verbose_name = _("Position")
        verbose_name_plural = _("Positions")

    def __str__(self) -> str:
        return f"{self.name} - {self.area.name}"


class Employee(
    core_models.BaseUserTracked,
    core_models.Person,
    TimeStampedModel,
):
    """Model to represent an employee of the organization."""

    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="employees",
        help_text=_("Position of the employee."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.EmployeeStatus.choices,
        default=choices.EmployeeStatus.ACTIVE,
        help_text=_("Current status of the employee."),
    )

    class Meta:
        managed = False
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["email"], name="unique_employee_email"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.paternal_last_name} - {self.position.name}"
