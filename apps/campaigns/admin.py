from django.contrib import admin

from apps.campaigns import models


class CSVContactInline(admin.TabularInline):
    """Inline admin for CSV Contacts."""

    model = models.CSVContact
    extra = 0
    readonly_fields = [
        "row_number",
        "full_name",
        "email",
        "phone",
        "telegram_id",
        "document_number",
        "amount",
        "is_valid",
        "validation_errors",
        "created",
        "modified",
    ]
    fields = [
        "row_number",
        "full_name",
        "email",
        "phone",
        "telegram_id",
        "document_number",
        "amount",
        "is_valid",
        "validation_errors",
    ]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.CampaignCSVFile)
class CampaignCSVFileAdmin(admin.ModelAdmin):
    """Admin configuration for CampaignCSVFile model."""

    list_display = [
        "id",
        "status",
        "channel",
        "validation_status",
        "total_contacts",
        "valid_contacts",
        "invalid_contacts",
        "execution_date",
        "created",
    ]
    list_filter = [
        "status",
        "channel",
        "validation_status",
        "use_payment_link",
        "created",
    ]
    search_fields = ["id"]
    readonly_fields = [
        "validation_status",
        "validation_result",
        "validated_at",
        "total_contacts",
        "valid_contacts",
        "invalid_contacts",
        "is_processing",
        "last_execution_at",
        "execution_count",
        "last_execution_result",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]
    inlines = [CSVContactInline]

    fieldsets = (
        (
            "File Information",
            {
                "fields": ("file",),
            },
        ),
        (
            "Validation",
            {
                "fields": (
                    "validation_status",
                    "validated_at",
                    "total_contacts",
                    "valid_contacts",
                    "invalid_contacts",
                    "validation_result",
                ),
            },
        ),
        (
            "Campaign Configuration",
            {
                "fields": (
                    "status",
                    "channel",
                    "use_payment_link",
                    "target_amount",
                    "average_cost",
                    "execution_date",
                ),
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
