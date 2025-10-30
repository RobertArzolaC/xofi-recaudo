from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.payments import models


class PaymentConceptAllocationInline(admin.TabularInline):
    """Inline admin for payment concept allocations."""

    model = models.PaymentConceptAllocation
    extra = 0
    fields = [
        "content_type",
        "object_id",
        "amount_applied",
        "allocation_type",
        "application_date",
        "notes",
    ]
    readonly_fields = ["application_date"]


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""

    list_display = [
        "partner",
        "payment_number",
        "payment_date",
        "amount",
        "payment_method",
        "total_allocated",
        "unallocated_amount",
        "status",
        "is_fully_allocated",
    ]
    list_filter = [
        "status",
        "payment_method",
        "payment_date",
        "partner",
    ]
    search_fields = [
        "partner__name",
        "partner__email",
        "payment_number",
        "reference_number",
    ]
    readonly_fields = [
        "total_allocated",
        "unallocated_amount",
        "is_fully_allocated",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]
    inlines = [PaymentConceptAllocationInline]

    fieldsets = (
        (None, {"fields": ("partner", "payment_number", "status")}),
        (
            _("Payment Details"),
            {
                "fields": (
                    "payment_date",
                    "amount",
                    "payment_method",
                    "reference_number",
                )
            },
        ),
        (
            _("Allocation Information"),
            {
                "fields": (
                    "total_allocated",
                    "unallocated_amount",
                    "is_fully_allocated",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Notes"),
            {"fields": ("notes",)},
        ),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.PaymentConceptAllocation)
class PaymentConceptAllocationAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentConceptAllocation model."""

    list_display = [
        "payment",
        "content_type",
        "concept_object",
        "amount_applied",
        "allocation_type",
        "application_date",
    ]
    list_filter = [
        "allocation_type",
        "application_date",
        "payment__status",
        "content_type",
    ]
    search_fields = [
        "payment__partner__name",
        "payment__partner__email",
        "payment__payment_number",
    ]
    readonly_fields = [
        "concept_object",
        "application_date",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "payment",
                    "content_type",
                    "object_id",
                    "amount_applied",
                    "allocation_type",
                )
            },
        ),
        (
            _("Dates"),
            {"fields": ("application_date",)},
        ),
        (
            _("Notes"),
            {"fields": ("notes",)},
        ),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.MagicPaymentLink)
class MagicPaymentLinkAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "partner",
        "amount",
        "status",
        "expires_at",
        "created",
    ]
    list_filter = ["status", "created", "expires_at"]
    search_fields = [
        "name",
        "partner__document_number",
        "partner__first_name",
        "token",
    ]
    readonly_fields = [
        "token",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]
    date_hierarchy = "created"

    fieldsets = (
        ("Información Básica", {"fields": ("partner", "name", "description")}),
        ("Configuración", {"fields": ("amount", "expires_at", "status")}),
        ("Link", {"fields": ("token",)}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        (
            "Auditoría",
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "modified_by",
                    "used_at",
                    "payment",
                ),
                "classes": ("collapse",),
            },
        ),
    )
