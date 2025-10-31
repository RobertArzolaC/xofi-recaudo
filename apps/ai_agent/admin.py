from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.ai_agent import models


class ConversationMessageInline(admin.TabularInline):
    """Inline for conversation messages."""

    model = models.ConversationMessage
    extra = 0
    readonly_fields = ["sender", "message", "intent", "created"]
    fields = ["sender", "message", "intent", "created"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    """Admin for AgentConversation model."""

    list_display = [
        "id",
        "partner",
        "telegram_chat_id",
        "telegram_username",
        "status",
        "authenticated",
        "last_interaction",
        "created",
    ]
    list_filter = ["status", "authenticated", "created"]
    search_fields = [
        "telegram_chat_id",
        "telegram_username",
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__document_number",
    ]
    readonly_fields = ["created", "modified", "last_interaction"]
    inlines = [ConversationMessageInline]
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "partner",
                    "telegram_chat_id",
                    "telegram_username",
                    "status",
                    "authenticated",
                )
            },
        ),
        (
            _("Context Data"),
            {
                "fields": ("context_data",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created", "modified", "last_interaction"),
            },
        ),
    )


@admin.register(models.ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    """Admin for ConversationMessage model."""

    list_display = [
        "id",
        "conversation",
        "sender",
        "intent",
        "message_preview",
        "created",
    ]
    list_filter = ["sender", "intent", "created"]
    search_fields = ["message", "conversation__telegram_chat_id"]
    readonly_fields = ["created", "modified"]

    def message_preview(self, obj):
        """Return a preview of the message."""
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message

    message_preview.short_description = _("Message Preview")
