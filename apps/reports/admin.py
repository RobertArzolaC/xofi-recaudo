from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.reports.models import Report, ReportFilter, ReportType


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for ReportType model.
    """

    list_display = [
        "name",
        "code",
        "model_name",
        "filter_count",
        "is_active",
        "created",
    ]
    list_filter = ["is_active", "created"]
    search_fields = ["name", "code", "description"]
    readonly_fields = ["created", "modified"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "code",
                    "model_name",
                    "is_active",
                )
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created", "modified"), "classes": ("collapse",)},
        ),
    )

    def filter_count(self, obj):
        """Display the number of filters for this report type."""
        count = obj.filters.filter(is_active=True).count()
        return format_html('<span class="badge badge-primary">{}</span>', count)

    filter_count.short_description = _("Active Filters")


@admin.register(ReportFilter)
class ReportFilterAdmin(admin.ModelAdmin):
    """
    Admin interface for ReportFilter model.
    """

    list_display = [
        "name",
        "report_type",
        "filter_type",
        "is_required",
        "order",
        "is_active",
    ]
    list_filter = ["filter_type", "is_required", "is_active", "report_type"]
    search_fields = ["name", "label", "field_name"]
    list_editable = ["order", "is_active"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "report_type",
                    "name",
                    "label",
                    "field_name",
                    "filter_type",
                )
            },
        ),
        (
            _("Configuration"),
            {"fields": ("options", "is_required", "order", "is_active")},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("report_type")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin interface for Report model.
    """

    list_display = [
        "title",
        "report_type",
        "format",
        "status_badge",
        "record_count",
        "file_size_display",
        "created",
    ]
    list_filter = ["status", "format", "report_type", "created", "completed_at"]
    search_fields = ["title", "description"]
    readonly_fields = [
        "celery_task_id",
        "started_at",
        "completed_at",
        "file_size",
        "record_count",
        "created",
        "modified",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "report_type",
                    "format",
                    "status",
                )
            },
        ),
        (
            _("Generation Info"),
            {
                "fields": ("filters", "celery_task_id", "error_message"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Results"),
            {
                "fields": ("file_path", "record_count", "file_size"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created", "modified", "started_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "created"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "report_type",
            )
        )

    def status_badge(self, obj):
        """Display status with color coding."""
        color_map = {
            "pending": "warning",
            "processing": "info",
            "completed": "success",
            "failed": "danger",
            "cancelled": "secondary",
        }
        color = color_map.get(obj.status, "secondary")
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")

    def file_size_display(self, obj):
        """Display file size in human readable format."""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"

    file_size_display.short_description = _("File Size")
