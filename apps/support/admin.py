from django.contrib import admin

from apps.support import models


class TicketCommentInline(admin.TabularInline):
    """Inline admin for TicketComment."""

    model = models.TicketComment
    extra = 0
    readonly_fields = ["created", "created_by"]
    fields = ["comment", "is_internal", "created", "created_by"]

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin interface for Ticket model."""

    list_display = [
        "id",
        "subject",
        "partner",
        "priority",
        "status",
        "assigned_to",
        "created",
    ]
    list_filter = [
        "status",
        "priority",
        "assigned_to",
        "created",
        "modified",
    ]
    search_fields = [
        "subject",
        "description",
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__document_number",
    ]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
    inlines = [TicketCommentInline]

    fieldsets = (
        (
            "Ticket Information",
            {
                "fields": (
                    "partner",
                    "subject",
                    "description",
                )
            },
        ),
        (
            "Status & Priority",
            {
                "fields": (
                    "status",
                    "priority",
                    "assigned_to",
                )
            },
        ),
        (
            "System Information",
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


@admin.register(models.TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """Admin interface for TicketComment model."""

    list_display = [
        "ticket",
        "comment_preview",
        "is_internal",
        "created_by",
        "created",
    ]
    list_filter = [
        "is_internal",
        "created",
    ]
    search_fields = [
        "comment",
        "ticket__subject",
    ]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]

    fieldsets = (
        (
            "Comment Information",
            {
                "fields": (
                    "ticket",
                    "comment",
                    "is_internal",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def comment_preview(self, obj):
        """Return a preview of the comment."""
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = "Comment"

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
