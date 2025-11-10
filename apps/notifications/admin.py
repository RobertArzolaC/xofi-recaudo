"""
Notifications Admin.

This module contains admin configurations for notification management.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.notifications import models


@admin.register(models.CampaignNotification)
class CampaignNotificationAdmin(admin.ModelAdmin):
    """Admin for CampaignNotification model."""

    list_display = [
        "id",
        "get_campaign_name",
        "get_recipient_name",
        "notification_type",
        "channel",
        "status",
        "scheduled_at",
        "sent_at",
        "attempt_count",
    ]
    list_filter = [
        "status",
        "channel",
        "notification_type",
        "scheduled_at",
        "sent_at",
        "created",
    ]
    search_fields = [
        "recipient_email",
        "recipient_phone",
        "message_content",
        "error_message",
    ]
    readonly_fields = [
        "campaign_type",
        "campaign_id",
        "recipient_type",
        "recipient_id",
        "sent_at",
        "attempt_count",
        "last_attempt_at",
        "created",
        "modified",
    ]
    fieldsets = (
        (
            _("Campaign Information"),
            {
                "fields": (
                    "campaign_type",
                    "campaign_id",
                )
            },
        ),
        (
            _("Recipient Information"),
            {
                "fields": (
                    "recipient_type",
                    "recipient_id",
                    "recipient_email",
                    "recipient_phone",
                )
            },
        ),
        (
            _("Notification Details"),
            {
                "fields": (
                    "notification_type",
                    "channel",
                    "status",
                    "message_content",
                )
            },
        ),
        (
            _("Scheduling"),
            {
                "fields": (
                    "scheduled_at",
                    "sent_at",
                )
            },
        ),
        (
            _("Payment Information"),
            {
                "fields": (
                    "total_debt_amount",
                    "included_payment_link",
                    "payment_link_url",
                )
            },
        ),
        (
            _("Error Handling"),
            {
                "fields": (
                    "error_message",
                    "attempt_count",
                    "last_attempt_at",
                )
            },
        ),
        (
            _("Tracking"),
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                )
            },
        ),
    )
    date_hierarchy = "created"
    ordering = ["-created"]

    def get_campaign_name(self, obj):
        """Get campaign name from generic foreign key."""
        try:
            return obj.campaign.name if obj.campaign else "-"
        except Exception:
            return "-"

    get_campaign_name.short_description = _("Campaign")

    def get_recipient_name(self, obj):
        """Get recipient name from generic foreign key."""
        try:
            if obj.recipient:
                return getattr(obj.recipient, "full_name", str(obj.recipient))
            return "-"
        except Exception:
            return "-"

    get_recipient_name.short_description = _("Recipient")

    def has_add_permission(self, request):
        """Disable manual creation of notifications."""
        return False


@admin.register(models.MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    """Admin for MessageTemplate model."""

    list_display = [
        "name",
        "template_type",
        "channel",
        "is_active",
        "include_payment_button",
        "created",
    ]
    list_filter = [
        "is_active",
        "template_type",
        "channel",
        "include_payment_button",
        "created",
    ]
    search_fields = [
        "name",
        "description",
        "message_body",
        "subject",
        "whatsapp_template_name",
    ]
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "description",
                    "template_type",
                    "channel",
                    "is_active",
                )
            },
        ),
        (
            _("Message Content"),
            {
                "fields": (
                    "subject",
                    "message_body",
                ),
                "description": _(
                    "Available placeholders: {partner_name}, {debt_amount}, "
                    "{payment_link}, {due_date}, {company_name}, {contact_phone}"
                ),
            },
        ),
        (
            _("WhatsApp Settings"),
            {
                "fields": (
                    "whatsapp_template_name",
                    "include_payment_button",
                    "payment_button_text",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Tracking"),
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                )
            },
        ),
    )
    readonly_fields = ["created", "modified"]
    date_hierarchy = "created"
    ordering = ["template_type", "channel", "name"]

    def save_model(self, request, obj, form, change):
        """Set user tracking fields."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
