from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.credits import choices, models


@admin.register(models.ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    """Admin configuration for ProductType model."""

    list_display = ["name", "is_active", "created", "created_by"]
    list_filter = ["is_active", "created"]
    search_fields = ["name", "description"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]

    fieldsets = (
        (None, {"fields": ("name", "description", "is_active")}),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    list_display = [
        "name",
        "product_type",
        "min_amount",
        "max_amount",
        "min_interest_rate",
        "max_interest_rate",
        "min_delinquency_rate",
        "max_delinquency_rate",
        "is_active",
    ]
    list_filter = [
        "product_type",
        "interest_type",
        "is_active",
        "created",
    ]
    search_fields = ["name", "description", "product_type__name"]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "product_type",
                    "is_active",
                )
            },
        ),
        (
            _("Amount Range"),
            {"fields": ("min_amount", "max_amount")},
        ),
        (
            _("Interest Rate"),
            {
                "fields": (
                    "min_interest_rate",
                    "max_interest_rate",
                    "interest_type",
                )
            },
        ),
        (
            _("Term"),
            {
                "fields": (
                    "min_term_duration",
                    "max_term_duration",
                    "payment_frequency",
                )
            },
        ),
        (
            _("Delinquency Rate"),
            {"fields": ("min_delinquency_rate", "max_delinquency_rate")},
        ),
        (
            _("Audit Information"),
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.Credit)
class CreditAdmin(admin.ModelAdmin):
    """Admin configuration for Credit model."""

    list_display = [
        "partner",
        "product",
        "amount",
        "interest_rate",
        "delinquency_rate",
        "term_duration",
        "status",
        "application_date",
        "outstanding_balance",
        "current_version",
    ]
    list_filter = [
        "status",
        "product__product_type",
        "product",
        "application_date",
        "approval_date",
    ]
    search_fields = [
        "partner__name",
        "partner__email",
        "product__name",
    ]
    readonly_fields = [
        "application_date",
        "total_interest",
        "total_repayment",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]

    fieldsets = (
        (None, {"fields": ("partner", "product", "status")}),
        (
            _("Credit Details"),
            {
                "fields": (
                    "amount",
                    "interest_rate",
                    "delinquency_rate",
                    "term_duration",
                    "payment_frequency",
                    "payment_amount",
                )
            },
        ),
        (
            _("Dates"),
            {
                "fields": (
                    "application_date",
                    "approval_date",
                    "disbursement_date",
                )
            },
        ),
        (
            _("Balance"),
            {"fields": ("outstanding_balance",)},
        ),
        (
            _("Calculations"),
            {
                "fields": ("total_interest", "total_repayment"),
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


class InstallmentInline(admin.TabularInline):
    """Inline admin for installments."""

    model = models.Installment
    extra = 0
    readonly_fields = [
        "is_overdue",
        "days_overdue",
        "amount_paid",
    ]
    fields = [
        "installment_number",
        "due_date",
        "installment_amount",
        "principal_amount",
        "interest_amount",
        "amount_paid",
        "balance_after",
        "status",
        "payment_date",
        "is_overdue",
        "days_overdue",
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.filter(
            status__in=[
                choices.InstallmentStatus.PENDING,
                choices.InstallmentStatus.OVERDUE,
                choices.InstallmentStatus.PARTIAL,
            ]
        ).order_by("installment_number")


@admin.register(models.Installment)
class InstallmentAdmin(admin.ModelAdmin):
    """Admin configuration for Installment model."""

    list_display = [
        "credit",
        "installment_number",
        "due_date",
        "installment_amount",
        "amount_paid",
        "remaining_balance",
        "status",
        "is_overdue",
        "days_overdue",
        "schedule_version",
    ]
    list_filter = ["status", "due_date", "payment_date", "credit__product"]
    search_fields = [
        "credit__partner__first_name",
        "credit__partner__paternal_last_name",
        "credit__partner__maternal_last_name",
        "credit__partner__document_number",
        "credit__partner__email",
    ]
    readonly_fields = [
        "is_overdue",
        "days_overdue",
        "amount_paid",
        "remaining_balance",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]

    fieldsets = (
        (None, {"fields": ("credit", "installment_number", "status")}),
        (
            _("Dates"),
            {"fields": ("due_date", "payment_date")},
        ),
        (
            _("Amounts"),
            {
                "fields": (
                    "installment_amount",
                    "principal_amount",
                    "interest_amount",
                    "balance_after",
                )
            },
        ),
        (
            _("Payment Status"),
            {
                "fields": (
                    "amount_paid",
                    "remaining_balance",
                    "is_overdue",
                    "days_overdue",
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


# Add inlines to CreditAdmin
CreditAdmin.inlines = [InstallmentInline]


@admin.register(models.CreditApplication)
class CreditApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for CreditApplication model."""

    list_display = [
        "partner",
        "product",
        "requested_amount",
        "proposed_interest_rate",
        "requested_term_duration",
        "requested_payment_frequency",
        "status",
        "created",
        "assigned_to",
    ]
    list_filter = [
        "status",
        "product__product_type",
        "product",
        "requested_payment_frequency",
        "created",
        "modified",
        "assigned_to",
    ]
    search_fields = [
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__email",
        "product__name",
    ]
    readonly_fields = [
        "estimated_payment_amount",
        "payment_schedule",
        "created",
        "modified",
        "created_by",
        "modified_by",
    ]

    fieldsets = (
        (None, {"fields": ("partner", "product", "status", "assigned_to")}),
        (
            _("Requested Terms"),
            {
                "fields": (
                    "requested_amount",
                    "proposed_interest_rate",
                    "requested_term_duration",
                    "requested_payment_frequency",
                    "proposed_delinquency_rate",
                    "possible_start_date",
                )
            },
        ),
        (
            _("Calculations"),
            {
                "fields": ("estimated_payment_amount",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Payment Schedule"),
            {
                "fields": ("payment_schedule",),
                "classes": ("collapse",),
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

    actions = [
        "submit_applications",
        "start_review_applications",
        "approve_applications",
        "reject_applications",
    ]

    def submit_applications(self, request, queryset):
        """Submit selected applications for review."""
        updated = 0
        for application in queryset:
            if application.submit(
                user=request.user, note="Submitted through admin interface"
            ):
                updated += 1

        self.message_user(
            request,
            _("Successfully submitted {} applications for review.").format(updated),
        )

    submit_applications.short_description = _("Submit selected applications")

    def start_review_applications(self, request, queryset):
        """Start review process for selected applications."""
        updated = 0
        for application in queryset:
            if application.start_review(
                user=request.user, note="Review started through admin interface"
            ):
                updated += 1

        self.message_user(
            request,
            _("Successfully started review for {} applications.").format(updated),
        )

    start_review_applications.short_description = _(
        "Start review for selected applications"
    )

    def approve_applications(self, request, queryset):
        """Approve selected applications."""
        updated = 0
        for application in queryset.filter(
            status__in=[
                models.choices.CreditApplicationStatus.SUBMITTED,
                models.choices.CreditApplicationStatus.UNDER_REVIEW,
            ]
        ):
            if application.approve(
                user=request.user, note="Approved through admin interface"
            ):
                updated += 1

        self.message_user(
            request,
            _("Successfully approved {} applications.").format(updated),
        )

    approve_applications.short_description = _("Approve selected applications")

    def reject_applications(self, request, queryset):
        """Reject selected applications with default reason."""
        updated = 0

        for application in queryset.filter(
            status__in=[
                models.choices.CreditApplicationStatus.SUBMITTED,
                models.choices.CreditApplicationStatus.UNDER_REVIEW,
            ]
        ):
            if application.reject(
                user=request.user, note="Application rejected by administrator"
            ):
                updated += 1

        self.message_user(
            request,
            _("Successfully rejected {} applications.").format(updated),
        )

    reject_applications.short_description = _("Reject selected applications")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("partner", "product", "assigned_to")
        )


@admin.register(models.CreditDisbursement)
class CreditDisbursementAdmin(admin.ModelAdmin):
    """Admin configuration for CreditDisbursement model."""

    list_display = [
        "credit",
        "disbursement_amount",
        "scheduled_date",
        "disbursement_method",
        "status",
        "reference_number",
    ]
    list_filter = [
        "status",
        "disbursement_method",
        "scheduled_date",
        "created",
    ]
    search_fields = [
        "credit__partner__first_name",
        "credit__partner__paternal_last_name",
        "credit__partner__email",
        "reference_number",
        "account_number",
        "check_number",
    ]
    readonly_fields = [
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
                    "credit",
                    "disbursement_amount",
                    "scheduled_date",
                    "disbursement_method",
                    "status",
                )
            },
        ),
        (
            _("Bank Transfer Details"),
            {
                "fields": (
                    "bank_name",
                    "account_number",
                    "account_holder_name",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Check Details"),
            {
                "fields": ("check_number",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Reference & Documents"),
            {
                "fields": (
                    "reference_number",
                    "receipt_document",
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

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("credit", "credit__partner")
