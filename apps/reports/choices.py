from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportStatus(models.TextChoices):
    """
    Report generation status choices.
    """

    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class ReportFormat(models.TextChoices):
    """
    Available export formats for reports.
    """

    CSV = "csv", _("CSV")
    EXCEL = "excel", _("Excel")


class FilterType(models.TextChoices):
    """
    Dynamic filter types for reports.
    """

    DATE = "date", _("Date")
    DATETIME = "datetime", _("DateTime")
    TEXT = "text", _("Text")
    NUMBER = "number", _("Number")
    SELECT = "select", _("Select")
    MULTISELECT = "multiselect", _("Multi Select")
    BOOLEAN = "boolean", _("Boolean")


class ReportTypeCode(models.TextChoices):
    """
    Report type codes for xofi-recaudo collection system.
    """

    # Collection Campaign Reports
    COLLECTION_CAMPAIGNS_SUMMARY = (
        "collection_campaigns_summary",
        _("Collection Campaigns Summary"),
    )
    CAMPAIGN_NOTIFICATIONS_DETAIL = (
        "campaign_notifications_detail",
        _("Campaign Notifications Detail"),
    )

    # Collection Group Reports
    COLLECTION_GROUP_EFFECTIVENESS = (
        "collection_group_effectiveness",
        _("Collection Group Effectiveness"),
    )

    # Recovery and Portfolio Reports
    COLLECTION_RECOVERY_REPORT = (
        "collection_recovery_report",
        _("Collection Recovery Report"),
    )
    COLLECTION_PORTFOLIO_AGING = (
        "collection_portfolio_aging",
        _("Collection Portfolio Aging"),
    )

    # Contactability Reports
    COLLECTION_CONTACTABILITY_REPORT = (
        "collection_contactability_report",
        _("Collection Contactability Report"),
    )

    # Payment Promise Reports
    PAYMENT_PROMISES_TRACKING = (
        "payment_promises_tracking",
        _("Payment Promises Tracking"),
    )

    # Payment Link Reports
    MAGIC_PAYMENT_LINKS_REPORT = (
        "magic_payment_links_report",
        _("Magic Payment Links Report"),
    )

    # KPI and Analytics Reports
    COLLECTION_MONTHLY_KPIS = (
        "collection_monthly_kpis",
        _("Collection Monthly KPIs"),
    )

    # Audit Reports
    COLLECTION_MANAGEMENT_AUDIT = (
        "collection_management_audit",
        _("Collection Management Audit"),
    )


class ReportSource(models.TextChoices):
    """
    Data sources for report generation.
    """

    XOFI_ERP = "xofi_erp", _("XOFI ERP")
    XOFI_COLLECTION = "xofi_collection", _("XOFI Collection")
