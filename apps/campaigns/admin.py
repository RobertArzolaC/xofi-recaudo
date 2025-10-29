from django.contrib import admin

from apps.campaigns import models


@admin.register(models.Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin configuration for Campaign model."""

    list_display = [
        "name",
        "status",
        "target_amount",
        "execution_time",
        "is_active",
        "created",
    ]
    list_filter = [
        "status",
        "use_payment_link",
        "notify_on_due_date",
        "notify_3_days_before",
        "notify_3_days_after",
        "notify_7_days_after",
        "created",
    ]
    search_fields = ["name", "description"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
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
                ),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("start_date", "end_date", "execution_time"),
            },
        ),
        (
            "Notification Configuration",
            {
                "fields": (
                    "notify_3_days_before",
                    "notify_on_due_date",
                    "notify_3_days_after",
                    "notify_7_days_after",
                    "use_payment_link",
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
