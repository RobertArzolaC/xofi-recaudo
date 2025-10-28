from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.compliance import models


@admin.register(models.Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Admin interface for Contribution model."""

    list_display = (
        "partner",
        "period_year",
        "period_month",
        "amount",
        "due_date",
        "status",
        "is_overdue",
    )
    list_filter = (
        "status",
        "period_year",
        "period_month",
        "due_date",
    )
    search_fields = (
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__document_number",
    )
    ordering = ("-period_year", "-period_month", "partner__first_name")
    date_hierarchy = "due_date"
    readonly_fields = ("created", "modified", "created_by", "modified_by")

    fieldsets = (
        (
            _("Partner Information"),
            {
                "fields": ("partner",),
            },
        ),
        (
            _("Period Information"),
            {
                "fields": ("period_year", "period_month"),
            },
        ),
        (
            _("Payment Information"),
            {
                "fields": (
                    "amount",
                    "due_date",
                    "status",
                ),
            },
        ),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_overdue(self, obj):
        """Display if contribution is overdue."""
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = _("Overdue")

    def save_model(self, request, obj, form, change):
        """Set user tracking fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.SocialSecurity)
class SocialSecurityAdmin(admin.ModelAdmin):
    """Admin interface for SocialSecurity model."""

    list_display = (
        "partner",
        "period_year",
        "period_month",
        "amount",
        "due_date",
        "status",
        "is_overdue",
    )
    list_filter = (
        "status",
        "period_year",
        "period_month",
        "due_date",
    )
    search_fields = (
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__document_number",
    )
    ordering = ("-period_year", "-period_month", "partner__first_name")
    date_hierarchy = "due_date"
    readonly_fields = ("created", "modified", "created_by", "modified_by")

    def is_overdue(self, obj):
        """Display if social security is overdue."""
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = _("Overdue")

    def save_model(self, request, obj, form, change):
        """Set user tracking fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    """Admin interface for Penalty model."""

    list_display = (
        "partner",
        "penalty_type",
        "amount",
        "issue_date",
        "due_date",
        "status",
        "is_overdue",
    )
    list_filter = (
        "penalty_type",
        "status",
        "issue_date",
        "due_date",
    )
    search_fields = (
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__document_number",
        "description",
    )
    ordering = ("-issue_date", "partner__first_name")
    date_hierarchy = "issue_date"
    readonly_fields = ("created", "modified", "created_by", "modified_by")

    fieldsets = (
        (
            _("Partner Information"),
            {
                "fields": ("partner",),
            },
        ),
        (
            _("Penalty Information"),
            {
                "fields": ("penalty_type", "description", "issue_date"),
            },
        ),
        (
            _("Payment Information"),
            {
                "fields": (
                    "amount",
                    "due_date",
                    "status",
                ),
            },
        ),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_overdue(self, obj):
        """Display if penalty is overdue."""
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = _("Overdue")

    def save_model(self, request, obj, form, change):
        """Set user tracking fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
