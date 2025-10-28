"""
Admin configuration for team models.
"""

from django.contrib import admin

from apps.team import models


@admin.register(models.Area)
class AreaAdmin(admin.ModelAdmin):
    """Admin configuration for Area model."""

    list_display = ["name", "description", "created", "created_by"]
    list_filter = ["created", "created_by"]
    search_fields = ["name", "description"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            "Audit",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position model."""

    list_display = ["name", "area", "description", "created", "created_by"]
    list_filter = ["area", "created", "created_by"]
    search_fields = ["name", "description", "area__name"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
    fieldsets = (
        (None, {"fields": ("name", "area", "description")}),
        (
            "Audit",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin configuration for Employee model."""

    list_display = [
        "full_name",
        "user",
        "position",
        "status",
        "email",
        "phone",
        "created",
    ]
    list_filter = [
        "status",
        "position__area",
        "position",
        "gender",
        "document_type",
        "created",
        "created_by",
    ]
    search_fields = [
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "email",
        "phone",
        "document_number",
        "user__username",
        "user__email",
    ]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "status",
                    "first_name",
                    "paternal_last_name",
                    "maternal_last_name",
                )
            },
        ),
        (
            "Document Information",
            {"fields": ("document_type", "document_number", "gender", "birth_date")},
        ),
        (
            "Position Information",
            {"fields": ("position",)},
        ),
        (
            "Contact Information",
            {"fields": ("email", "phone")},
        ),
        (
            "Address Information",
            {
                "fields": (
                    "address",
                    "zip_code",
                    "country",
                    "region",
                    "subregion",
                    "city",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
