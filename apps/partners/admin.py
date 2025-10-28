from django.contrib import admin

from apps.partners import models


@admin.register(models.Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    """Admin interface for Applicant model."""

    list_display = [
        "full_name",
        "external_id",
        "document_type",
        "document_number",
        "status",
        "country",
        "created",
    ]
    list_filter = [
        "status",
        "document_type",
        "gender",
        "country",
        "region",
        "created",
        "modified",
    ]
    search_fields = [
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "external_id",
        "document_number",
        "email",
        "phone",
    ]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "external_id",
                    "first_name",
                    "paternal_last_name",
                    "maternal_last_name",
                    "document_type",
                    "document_number",
                    "gender",
                    "birth_date",
                )
            },
        ),
        (
            "Contact Information",
            {"fields": ("phone", "email")},
        ),
        (
            "Address Information",
            {
                "fields": (
                    "address",
                    "country",
                    "region",
                    "subregion",
                    "city",
                    "zip_code",
                )
            },
        ),
        (
            "Status Information",
            {"fields": ("status",)},
        ),
        (
            "System Information",
            {
                "fields": ("created", "modified"),
                "classes": ("collapse",),
            },
        ),
    )

    def full_name(self, obj):
        """Return the full name of the applicant."""
        return obj.full_name

    full_name.short_description = "Full Name"
    full_name.admin_order_field = "first_name"


@admin.register(models.Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Admin interface for Partner model."""

    list_display = [
        "full_name",
        "document_type",
        "document_number",
        "status",
        "country",
        "created",
    ]
    list_filter = [
        "status",
        "document_type",
        "gender",
        "country",
        "region",
        "created",
        "modified",
    ]
    search_fields = [
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "document_number",
        "email",
        "phone",
    ]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "paternal_last_name",
                    "maternal_last_name",
                    "document_type",
                    "document_number",
                    "gender",
                    "birth_date",
                )
            },
        ),
        (
            "Contact Information",
            {"fields": ("phone", "email")},
        ),
        (
            "Address Information",
            {
                "fields": (
                    "address",
                    "country",
                    "region",
                    "subregion",
                    "city",
                    "zip_code",
                )
            },
        ),
        (
            "Status Information",
            {"fields": ("status",)},
        ),
        (
            "System Information",
            {
                "fields": ("created", "modified"),
                "classes": ("collapse",),
            },
        ),
    )

    def full_name(self, obj):
        """Return the full name of the partner."""
        return obj.full_name

    full_name.short_description = "Full Name"
    full_name.admin_order_field = "first_name"


@admin.register(models.PartnerEmploymentInfo)
class PartnerEmploymentInfoAdmin(admin.ModelAdmin):
    """Admin interface for PartnerEmploymentInfo model."""

    list_display = [
        "partner",
        "occupation",
        "employment_type",
        "is_currently_employed",
        "workplace_name",
        "contract_type",
        "base_salary",
        "created",
    ]
    list_filter = [
        "employment_type",
        "contract_type",
        "work_schedule",
        "education_level",
        "is_currently_employed",
        "salary_frequency",
        "created",
        "modified",
    ]
    search_fields = [
        "partner__first_name",
        "partner__paternal_last_name",
        "partner__maternal_last_name",
        "occupation",
        "profession",
        "workplace_name",
        "job_position",
        "supervisor_name",
    ]
    readonly_fields = ["created", "modified", "created_by", "modified_by"]

    fieldsets = (
        (
            "Partner Information",
            {"fields": ("partner",)},
        ),
        (
            "Professional Information",
            {
                "fields": (
                    "occupation",
                    "profession",
                    "education_level",
                    "employment_type",
                    "is_currently_employed",
                )
            },
        ),
        (
            "Workplace Information",
            {
                "fields": (
                    "workplace_name",
                    "workplace_address",
                    "other_workplace",
                    "job_position",
                    "department",
                )
            },
        ),
        (
            "Contract Information",
            {
                "fields": (
                    "contract_type",
                    "contract_start_date",
                    "contract_end_date",
                    "work_schedule",
                    "weekly_hours",
                )
            },
        ),
        (
            "Income Information",
            {
                "fields": (
                    "base_salary",
                    "salary_frequency",
                    "additional_income",
                    "total_monthly_income",
                )
            },
        ),
        (
            "Work Contact Information",
            {
                "fields": (
                    "work_phone",
                    "work_email",
                    "supervisor_name",
                )
            },
        ),
        (
            "Additional Information",
            {"fields": ("notes",)},
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


@admin.register(models.Prospect)
class ProspectAdmin(admin.ModelAdmin):
    """Admin interface for Prospect model."""

    list_display = [
        "full_name",
        "document_type",
        "document_number",
        "status",
        "email",
        "phone",
        "source",
        "assigned_to",
        "created",
    ]
    list_filter = [
        "status",
        "document_type",
        "source",
        "assigned_to",
        "contacted_at",
        "created",
        "modified",
    ]
    search_fields = [
        "first_name",
        "last_name",
        "document_number",
        "email",
        "phone",
    ]
    readonly_fields = [
        "created",
        "modified",
        "created_by",
        "modified_by",
        "ip_address",
        "user_agent",
    ]

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "document_type",
                    "document_number",
                    "birth_date",
                )
            },
        ),
        (
            "Contact Information",
            {"fields": ("email", "phone")},
        ),
        (
            "Status Information",
            {
                "fields": (
                    "status",
                    "assigned_to",
                    "contacted_at",
                )
            },
        ),
        (
            "Source Information",
            {
                "fields": (
                    "source",
                    "ip_address",
                    "user_agent",
                )
            },
        ),
        (
            "Additional Information",
            {"fields": ("notes",)},
        ),
        (
            "System Information",
            {
                "fields": ("created", "modified", "created_by", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def full_name(self, obj):
        """Return the full name of the prospect."""
        return obj.full_name

    full_name.short_description = "Full Name"
    full_name.admin_order_field = "first_name"

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
