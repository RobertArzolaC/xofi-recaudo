from typing import Any, Dict, List

from apps.reports import choices
from apps.reports.generators.analytics import (
    CollectionManagementAuditReportGenerator,
    CollectionMonthlyKPIsReportGenerator,
)
from apps.reports.generators.base import BaseReportGenerator
from apps.reports.generators.campaigns import (
    CampaignNotificationsDetailReportGenerator,
    CollectionCampaignsSummaryReportGenerator,
)
from apps.reports.generators.groups import CollectionGroupEffectivenessReportGenerator
from apps.reports.generators.payments import (
    MagicPaymentLinksReportGenerator,
    PaymentPromisesTrackingReportGenerator,
)
from apps.reports.generators.portfolio import (
    CollectionContactabilityReportGenerator,
    CollectionPortfolioAgingReportGenerator,
    CollectionRecoveryReportGenerator,
)


class ReportGeneratorFactory:
    """
    Factory class to create appropriate report generators.
    """

    _generators = {
        # Campaign Reports
        choices.ReportTypeCode.COLLECTION_CAMPAIGNS_SUMMARY: CollectionCampaignsSummaryReportGenerator,
        choices.ReportTypeCode.CAMPAIGN_NOTIFICATIONS_DETAIL: CampaignNotificationsDetailReportGenerator,
        # Group Reports
        choices.ReportTypeCode.COLLECTION_GROUP_EFFECTIVENESS: CollectionGroupEffectivenessReportGenerator,
        # Recovery and Portfolio Reports
        choices.ReportTypeCode.COLLECTION_RECOVERY_REPORT: CollectionRecoveryReportGenerator,
        choices.ReportTypeCode.COLLECTION_PORTFOLIO_AGING: CollectionPortfolioAgingReportGenerator,
        # Contactability Reports
        choices.ReportTypeCode.COLLECTION_CONTACTABILITY_REPORT: CollectionContactabilityReportGenerator,
        # Payment Reports
        choices.ReportTypeCode.PAYMENT_PROMISES_TRACKING: PaymentPromisesTrackingReportGenerator,
        choices.ReportTypeCode.MAGIC_PAYMENT_LINKS_REPORT: MagicPaymentLinksReportGenerator,
        # Analytics and KPIs
        choices.ReportTypeCode.COLLECTION_MONTHLY_KPIS: CollectionMonthlyKPIsReportGenerator,
        # Audit Reports
        choices.ReportTypeCode.COLLECTION_MANAGEMENT_AUDIT: CollectionManagementAuditReportGenerator,
    }

    @classmethod
    def create_generator(
        cls, report_type: str, filters: Dict[str, Any]
    ) -> BaseReportGenerator:
        """
        Create a report generator for the given report type.
        """
        generator_class = cls._generators.get(report_type)
        if not generator_class:
            raise ValueError(f"No generator found for report type: {report_type}")

        return generator_class(report_type, filters)

    @classmethod
    def get_available_report_types(cls) -> List[str]:
        """
        Get list of available report types.
        """
        return list(cls._generators.keys())

    @classmethod
    def register_generator(cls, report_type: str, generator_class: type) -> None:
        """
        Register a new report generator.
        """
        cls._generators[report_type] = generator_class
