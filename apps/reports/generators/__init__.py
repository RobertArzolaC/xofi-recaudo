"""
Report generators package.
"""

from apps.reports.generators.analytics import (
    CollectionManagementAuditReportGenerator,
    CollectionMonthlyKPIsReportGenerator,
)
from apps.reports.generators.base import BaseReportGenerator
from apps.reports.generators.campaigns import (
    CampaignNotificationsDetailReportGenerator,
    CollectionCampaignsSummaryReportGenerator,
)
from apps.reports.generators.factory import ReportGeneratorFactory
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

__all__ = [
    "BaseReportGenerator",
    "ReportGeneratorFactory",
    # Campaign Reports
    "CollectionCampaignsSummaryReportGenerator",
    "CampaignNotificationsDetailReportGenerator",
    # Group Reports
    "CollectionGroupEffectivenessReportGenerator",
    # Portfolio and Recovery Reports
    "CollectionRecoveryReportGenerator",
    "CollectionPortfolioAgingReportGenerator",
    "CollectionContactabilityReportGenerator",
    # Payment Reports
    "PaymentPromisesTrackingReportGenerator",
    "MagicPaymentLinksReportGenerator",
    # Analytics and KPIs
    "CollectionMonthlyKPIsReportGenerator",
    "CollectionManagementAuditReportGenerator",
]
