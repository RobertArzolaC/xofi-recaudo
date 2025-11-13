from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core.models import NameDescription
from apps.reports import choices


class ReportType(NameDescription, TimeStampedModel):
    """
    Defines different types of reports available in the system.
    """

    code = models.CharField(
        _("Code"),
        max_length=50,
        choices=choices.ReportTypeCode.choices,
        unique=True,
    )
    model_name = models.CharField(_("Model Name"), max_length=100)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("Report Type")
        verbose_name_plural = _("Report Types")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ReportFilter(models.Model):
    """
    Dynamic filters available for report types.
    """

    report_type = models.ForeignKey(
        ReportType,
        on_delete=models.CASCADE,
        related_name="filters",
        verbose_name=_("Report Type"),
    )
    name = models.CharField(_("Name"), max_length=100)
    label = models.CharField(_("Label"), max_length=200)
    field_name = models.CharField(_("Field Name"), max_length=100)
    filter_type = models.CharField(
        _("Filter Type"), max_length=20, choices=choices.FilterType.choices
    )
    options = models.JSONField(_("Options"), default=dict, blank=True)
    is_required = models.BooleanField(_("Is Required"), default=False)
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("Report Filter")
        verbose_name_plural = _("Report Filters")
        ordering = ["report_type", "order", "name"]
        unique_together = ["report_type", "name"]

    def __str__(self) -> str:
        return f"{self.report_type.name} - {self.label}"


class Report(TimeStampedModel):
    """
    Represents a generated report in the system.
    """

    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    report_type = models.ForeignKey(
        ReportType,
        on_delete=models.CASCADE,
        verbose_name=_("Report Type"),
        related_name="reports",
    )
    format = models.CharField(
        _("Format"), max_length=20, choices=choices.ReportFormat.choices
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.ReportStatus.choices,
        default=choices.ReportStatus.PENDING,
    )
    filters = models.JSONField(
        _("Filters"),
        default=dict,
        blank=True,
        help_text=_("JSON filters applied to generate the report"),
    )
    file_path = models.FileField(
        _("File"), upload_to="reports/%Y/%m/", blank=True, null=True
    )
    celery_task_id = models.CharField(
        _("Celery Task ID"), max_length=255, blank=True, null=True
    )
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(
        _("Completed at"), null=True, blank=True
    )
    error_message = models.TextField(_("Error Message"), blank=True)
    file_size = models.BigIntegerField(_("File Size"), null=True, blank=True)
    record_count = models.PositiveIntegerField(
        _("Record Count"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"{self.title} - {self.get_status_display()}"

    @property
    def is_processing(self) -> bool:
        return self.status in [
            choices.ReportStatus.PENDING,
            choices.ReportStatus.PROCESSING,
        ]

    @property
    def is_completed(self) -> bool:
        return self.status == choices.ReportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == choices.ReportStatus.FAILED

    @property
    def duration(self) -> int:
        """Returns duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return 0

    @property
    def file_size_display(self) -> str:
        """Returns file size in human readable format."""
        if self.file_size:
            if self.file_size < 1024:
                return f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                return f"{self.file_size / 1024:.2f} KB"
            else:
                return f"{self.file_size / (1024 * 1024):.2f} MB"
        return "-"

    @property
    def duration_display(self) -> str:
        """Returns duration in human readable format."""
        duration = self.duration
        if duration < 60:
            return f"{duration} seconds" if duration != 1 else "1 second"
        else:
            minutes = duration / 60
            return f"{minutes:.1f} minutes" if minutes != 1 else "1 minute"
