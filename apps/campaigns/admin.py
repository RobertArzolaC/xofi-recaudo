from django.contrib import admin

from apps.campaigns import models


@admin.register(models.Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin configuration for Campaign model."""

    list_display = [
        "name",
        "status",
        "channel",
        "target_amount",
        "execution_date",
        "is_processing",
        "execution_count",
        "is_active",
        "created",
    ]
    list_filter = [
        "status",
        "channel",
        "is_processing",
        "use_payment_link",
        "created",
    ]
    search_fields = ["name", "description"]
    readonly_fields = [
        "created",
        "modified",
        "created_by",
        "modified_by",
        "is_processing",
        "last_execution_at",
        "execution_count",
        "last_execution_result",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "description",
                    "group",
                    "status",
                    "target_amount",
                    "average_cost",
                ),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("execution_date",),
            },
        ),
        (
            "Notification Configuration",
            {
                "fields": ("channel", "use_payment_link"),
            },
        ),
        (
            "Execution Tracking",
            {
                "fields": (
                    "is_processing",
                    "last_execution_at",
                    "execution_count",
                    "last_execution_result",
                ),
            },
        ),
        (
            "Audit Information",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin configuration for Group model."""

    list_display = ["name", "priority", "partner_count", "created"]
    list_filter = ["priority", "created"]
    search_fields = ["name", "description"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
    filter_horizontal = ["partners"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("name", "description", "priority"),
            },
        ),
        (
            "Partners",
            {
                "fields": ("partners",),
            },
        ),
        (
            "Audit Information",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
