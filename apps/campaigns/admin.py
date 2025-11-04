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


@admin.register(models.CampaignNotification)
class CampaignNotificationAdmin(admin.ModelAdmin):
    """Admin configuration for CampaignNotification model."""

    list_display = [
        "campaign",
        "partner",
        "notification_type",
        "channel",
        "status",
        "scheduled_at",
        "sent_at",
        "attempt_count",
    ]
    list_filter = [
        "status",
        "notification_type",
        "channel",
        "included_payment_link",
        "campaign__status",
        "created",
        "scheduled_at",
        "sent_at",
    ]
    search_fields = [
        "campaign__name",
        "partner__name",
        "partner__email",
        "recipient_email",
        "recipient_phone",
    ]
    readonly_fields = [
        "created",
        "modified",
        "created_by",
        "modified_by",
        "sent_at",
        "last_attempt_at",
    ]
    raw_id_fields = ["campaign", "partner"]
    date_hierarchy = "scheduled_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "campaign",
                    "partner",
                    "notification_type",
                    "channel",
                    "status",
                ),
            },
        ),
        (
            "Scheduling & Delivery",
            {
                "fields": (
                    "scheduled_at",
                    "sent_at",
                    "attempt_count",
                    "last_attempt_at",
                ),
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "recipient_email",
                    "recipient_phone",
                ),
            },
        ),
        (
            "Message Content",
            {
                "fields": (
                    "message_content",
                    "error_message",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Payment Information",
            {
                "fields": (
                    "total_debt_amount",
                    "included_payment_link",
                    "payment_link_url",
                ),
                "classes": ("collapse",),
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

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("campaign", "partner", "created_by", "modified_by")
        )


@admin.register(models.MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for MessageTemplate model."""

    list_display = [
        "name",
        "template_type",
        "channel",
        "is_active",
        "include_payment_button",
        "created",
    ]
    list_filter = [
        "template_type",
        "channel",
        "is_active",
        "include_payment_button",
        "created",
    ]
    search_fields = ["name", "description", "message_body"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "description",
                    "template_type",
                    "channel",
                    "is_active",
                ),
            },
        ),
        (
            "Message Content",
            {
                "fields": (
                    "subject",
                    "message_body",
                ),
                "description": (
                    "Available placeholders: {partner_name}, {debt_amount}, "
                    "{credit_debt}, {credit_debt_count}, {contribution_debt}, "
                    "{contribution_debt_count}, {social_security_debt}, "
                    "{social_security_debt_count}, {penalty_debt}, {penalty_debt_count}, "
                    "{payment_link}, {campaign_name}, {company_name}, {contact_phone}"
                ),
            },
        ),
        (
            "WhatsApp Configuration",
            {
                "fields": ("whatsapp_template_name",),
                "classes": ("collapse",),
            },
        ),
        (
            "Payment Button Configuration",
            {
                "fields": (
                    "include_payment_button",
                    "payment_button_text",
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
