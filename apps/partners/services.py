from decimal import Decimal
from typing import Dict, List

from django.db.models import Count, QuerySet, Sum
from django.utils import timezone

# Compliance debts overdue
from apps.compliance.choices import ComplianceStatus
from apps.compliance.models import (
    Contribution,
    Penalty,
    SocialSecurity,
)

# Credit installments overdue
from apps.credits.choices import InstallmentStatus
from apps.credits.models import Installment
from apps.partners import models


class PartnerDebtService:
    """Service class for calculating partner debt information."""

    @staticmethod
    def calculate_total_outstanding_debt(partners: QuerySet) -> Decimal:
        """
        Calculate the total overdue debt for a collection of partners.

        Args:
            partners: QuerySet of Partner objects

        Returns:
            Decimal: Total debt amount across all partners
        """
        try:
            total_debt = Decimal("0.00")
            today = timezone.now().date()

            overdue_installments = Installment.objects.filter(
                credit__partner__in=partners,
                due_date__lt=today,
                status__in=[
                    InstallmentStatus.PENDING,
                    InstallmentStatus.PARTIAL,
                    InstallmentStatus.OVERDUE,
                ],
            )

            credit_debt = overdue_installments.aggregate(
                total=Sum("installment_amount")
            )["total"] or Decimal("0.00")
            total_debt += credit_debt

            overdue_status = [
                ComplianceStatus.PENDING,
                ComplianceStatus.OVERDUE,
                ComplianceStatus.PARTIAL,
            ]

            # Contributions overdue
            overdue_contributions = Contribution.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            contribution_debt = overdue_contributions.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
            total_debt += contribution_debt

            # Social Security overdue
            overdue_social_security = SocialSecurity.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            social_security_debt = overdue_social_security.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
            total_debt += social_security_debt

            # Penalties overdue
            overdue_penalties = Penalty.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            penalty_debt = overdue_penalties.aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")
            total_debt += penalty_debt

            return total_debt

        except Exception:
            return Decimal("0.00")

    @staticmethod
    def count_overdue_obligations(partners: QuerySet) -> int:
        """
        Count the total number of overdue obligations for a collection of partners.

        Args:
            partners: QuerySet of Partner objects

        Returns:
            int: Total count of overdue obligations
        """
        try:
            today = timezone.now().date()
            total_count = 0

            overdue_installments = Installment.objects.filter(
                credit__partner__in=partners,
                due_date__lt=today,
                status__in=[
                    InstallmentStatus.PENDING,
                    InstallmentStatus.PARTIAL,
                    InstallmentStatus.OVERDUE,
                ],
            ).count()
            total_count += overdue_installments

            overdue_status = [
                ComplianceStatus.PENDING,
                ComplianceStatus.OVERDUE,
                ComplianceStatus.PARTIAL,
            ]

            overdue_contributions = Contribution.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            ).count()
            total_count += overdue_contributions

            overdue_social_security = SocialSecurity.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            ).count()
            total_count += overdue_social_security

            overdue_penalties = Penalty.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            ).count()
            total_count += overdue_penalties

            return total_count

        except Exception:
            return 0

    @staticmethod
    def get_debt_summary(partners: QuerySet) -> Dict:
        """
        Get a detailed summary of overdue debts for a collection of partners.

        Args:
            partners: QuerySet of Partner objects

        Returns:
            Dict: Detailed debt summary with breakdowns by type
        """
        try:
            today = timezone.now().date()
            total_debt = Decimal("0.00")

            overdue_installments = Installment.objects.filter(
                credit__partner__in=partners,
                due_date__lt=today,
                status__in=[
                    InstallmentStatus.PENDING,
                    InstallmentStatus.PARTIAL,
                    InstallmentStatus.OVERDUE,
                ],
            )

            credit_summary = overdue_installments.aggregate(
                total=Sum("installment_amount"), count=Count("id")
            )
            credit_debt = credit_summary["total"] or Decimal("0.00")
            credit_count = credit_summary["count"] or 0
            total_debt += credit_debt

            overdue_status = [
                ComplianceStatus.PENDING,
                ComplianceStatus.OVERDUE,
                ComplianceStatus.PARTIAL,
            ]

            # Contributions
            overdue_contributions = Contribution.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            contribution_summary = overdue_contributions.aggregate(
                total=Sum("amount"), count=Count("id")
            )
            contribution_debt = contribution_summary["total"] or Decimal("0.00")
            contribution_count = contribution_summary["count"] or 0
            total_debt += contribution_debt

            # Social Security
            overdue_social_security = SocialSecurity.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            social_security_summary = overdue_social_security.aggregate(
                total=Sum("amount"), count=Count("id")
            )
            social_security_debt = social_security_summary["total"] or Decimal(
                "0.00"
            )
            social_security_count = social_security_summary["count"] or 0
            total_debt += social_security_debt

            # Penalties
            overdue_penalties = Penalty.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=overdue_status,
            )
            penalty_summary = overdue_penalties.aggregate(
                total=Sum("amount"), count=Count("id")
            )
            penalty_debt = penalty_summary["total"] or Decimal("0.00")
            penalty_count = penalty_summary["count"] or 0
            total_debt += penalty_debt

            # Count partners with any overdue debt
            partners_with_debt = set()

            # Partners with overdue installments
            partners_with_debt.update(
                overdue_installments.values_list(
                    "credit__partner_id", flat=True
                )
            )

            # Partners with overdue compliance obligations
            partners_with_debt.update(
                overdue_contributions.values_list("partner_id", flat=True)
            )
            partners_with_debt.update(
                overdue_social_security.values_list("partner_id", flat=True)
            )
            partners_with_debt.update(
                overdue_penalties.values_list("partner_id", flat=True)
            )

            return {
                "total_debt": total_debt,
                "credit_debt": credit_debt,
                "contribution_debt": contribution_debt,
                "social_security_debt": social_security_debt,
                "penalty_debt": penalty_debt,
                "overdue_installments": credit_count,
                "overdue_contributions": contribution_count,
                "overdue_social_security": social_security_count,
                "overdue_penalties": penalty_count,
                "partners_with_debt": len(partners_with_debt),
            }
        except Exception:
            return {
                "total_debt": Decimal("0.00"),
                "credit_debt": Decimal("0.00"),
                "contribution_debt": Decimal("0.00"),
                "social_security_debt": Decimal("0.00"),
                "penalty_debt": Decimal("0.00"),
                "overdue_installments": 0,
                "overdue_contributions": 0,
                "overdue_social_security": 0,
                "overdue_penalties": 0,
                "partners_with_debt": 0,
            }

    @staticmethod
    def get_partners_debt_detail(partners: QuerySet) -> List[Dict]:
        """
        Get detailed debt information for each partner in the collection.

        Args:
            partners: QuerySet of Partner objects

        Returns:
            List[Dict]: List of debt details for each partner with debt
        """
        try:
            partners_detail = []
            today = timezone.now().date()

            for partner in partners:
                partner_debt = {
                    "partner": partner,
                    "total_debt": Decimal("0.00"),
                    "credit_debt": Decimal("0.00"),
                    "contribution_debt": Decimal("0.00"),
                    "social_security_debt": Decimal("0.00"),
                    "penalty_debt": Decimal("0.00"),
                }

                overdue_installments = Installment.objects.filter(
                    credit__partner=partner,
                    due_date__lt=today,
                    status__in=[
                        InstallmentStatus.PENDING,
                        InstallmentStatus.PARTIAL,
                        InstallmentStatus.OVERDUE,
                    ],
                )
                credit_debt = overdue_installments.aggregate(
                    total=Sum("installment_amount")
                )["total"] or Decimal("0.00")
                partner_debt["overdue_installments"] = (
                    overdue_installments.count()
                )
                partner_debt["credit_debt"] = credit_debt
                partner_debt["total_debt"] += credit_debt

                overdue_status = [
                    ComplianceStatus.PENDING,
                    ComplianceStatus.OVERDUE,
                    ComplianceStatus.PARTIAL,
                ]

                # Contributions
                overdue_contributions = Contribution.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                )
                contribution_debt = overdue_contributions.aggregate(
                    total=Sum("amount")
                )["total"] or Decimal("0.00")
                partner_debt["overdue_contributions"] = (
                    overdue_contributions.count()
                )
                partner_debt["contribution_debt"] = contribution_debt
                partner_debt["total_debt"] += contribution_debt

                # Social Security
                overdue_social_security = SocialSecurity.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                )
                social_security_debt = overdue_social_security.aggregate(
                    total=Sum("amount")
                )["total"] or Decimal("0.00")
                partner_debt["overdue_social_security"] = (
                    overdue_social_security.count()
                )
                partner_debt["social_security_debt"] = social_security_debt
                partner_debt["total_debt"] += social_security_debt

                # Penalties
                overdue_penalties = Penalty.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                )
                penalty_debt = overdue_penalties.aggregate(total=Sum("amount"))[
                    "total"
                ] or Decimal("0.00")
                partner_debt["overdue_penalties"] = overdue_penalties.count()
                partner_debt["penalty_debt"] = penalty_debt
                partner_debt["total_debt"] += penalty_debt

                # Only include partners with debt
                if partner_debt["total_debt"] > 0:
                    partners_detail.append(partner_debt)

            return partners_detail

        except Exception:
            return []

    @staticmethod
    def get_single_partner_debt_detail(partner) -> Dict:
        """
        Get detailed debt information for a single partner.

        Args:
            partner: Partner instance

        Returns:
            Dict: Debt details for the partner
        """

        if isinstance(partner, QuerySet):
            # If a QuerySet is passed, get the first partner
            partner = partner.first()

        if not partner:
            return {
                "partner": None,
                "total_debt": Decimal("0.00"),
                "credit_debt": Decimal("0.00"),
                "contribution_debt": Decimal("0.00"),
                "social_security_debt": Decimal("0.00"),
                "penalty_debt": Decimal("0.00"),
            }

        partner_queryset = models.Partner.objects.filter(id=partner.id)
        debt_details = PartnerDebtService.get_partners_debt_detail(
            partner_queryset
        )

        if debt_details:
            return debt_details[0]
        else:
            return {
                "partner": partner,
                "total_debt": Decimal("0.00"),
                "credit_debt": Decimal("0.00"),
                "contribution_debt": Decimal("0.00"),
                "social_security_debt": Decimal("0.00"),
                "penalty_debt": Decimal("0.00"),
            }

    @staticmethod
    def get_partner_overdue_debts(partner, include_upcoming=False, days_ahead=30):
        """
        Get all individual overdue debts for a partner.

        Args:
            partner: Partner instance
            include_upcoming: Whether to include upcoming debts (default False)
            days_ahead: Number of days to look ahead for upcoming debts (default 30)

        Returns:
            Dict: Dictionary with lists of debt objects by type
        """
        today = timezone.now().date()
        future_date = today + timezone.timedelta(days=days_ahead) if include_upcoming else today

        overdue_status = [
            ComplianceStatus.PENDING,
            ComplianceStatus.OVERDUE,
            ComplianceStatus.PARTIAL,
        ]

        # Get overdue installments
        overdue_installments = Installment.objects.filter(
            credit__partner=partner,
            due_date__lt=today,
            status__in=[
                InstallmentStatus.PENDING,
                InstallmentStatus.PARTIAL,
                InstallmentStatus.OVERDUE,
            ],
        ).order_by("due_date")

        # Get upcoming installments if requested
        upcoming_installments = []
        if include_upcoming:
            upcoming_installments = Installment.objects.filter(
                credit__partner=partner,
                due_date__gte=today,
                due_date__lte=future_date,
                status=InstallmentStatus.PENDING,
            ).order_by("due_date")

        # Get overdue contributions
        overdue_contributions = Contribution.objects.filter(
            partner=partner,
            due_date__lt=today,
            status__in=overdue_status,
        ).order_by("due_date")

        # Get upcoming contributions if requested
        upcoming_contributions = []
        if include_upcoming:
            upcoming_contributions = Contribution.objects.filter(
                partner=partner,
                due_date__gte=today,
                due_date__lte=future_date,
                status=ComplianceStatus.PENDING,
            ).order_by("due_date")

        # Get overdue social security
        overdue_social_security = SocialSecurity.objects.filter(
            partner=partner,
            due_date__lt=today,
            status__in=overdue_status,
        ).order_by("due_date")

        # Get upcoming social security if requested
        upcoming_social_security = []
        if include_upcoming:
            upcoming_social_security = SocialSecurity.objects.filter(
                partner=partner,
                due_date__gte=today,
                due_date__lte=future_date,
                status=ComplianceStatus.PENDING,
            ).order_by("due_date")

        # Get overdue penalties
        overdue_penalties = Penalty.objects.filter(
            partner=partner,
            due_date__lt=today,
            status__in=overdue_status,
        ).order_by("due_date")

        # Get upcoming penalties if requested
        upcoming_penalties = []
        if include_upcoming:
            upcoming_penalties = Penalty.objects.filter(
                partner=partner,
                due_date__gte=today,
                due_date__lte=future_date,
                status=ComplianceStatus.PENDING,
            ).order_by("due_date")

        # Combine all debts
        all_debts = (
            list(overdue_installments)
            + list(upcoming_installments)
            + list(overdue_contributions)
            + list(upcoming_contributions)
            + list(overdue_social_security)
            + list(upcoming_social_security)
            + list(overdue_penalties)
            + list(upcoming_penalties)
        )

        # Sort all debts by due date
        all_debts.sort(key=lambda x: x.due_date)

        return {
            "installments": {
                "overdue": list(overdue_installments),
                "upcoming": list(upcoming_installments),
            },
            "contributions": {
                "overdue": list(overdue_contributions),
                "upcoming": list(upcoming_contributions),
            },
            "social_security": {
                "overdue": list(overdue_social_security),
                "upcoming": list(upcoming_social_security),
            },
            "penalties": {
                "overdue": list(overdue_penalties),
                "upcoming": list(upcoming_penalties),
            },
            "all_debts": all_debts,
        }

    @staticmethod
    def get_partner_debt_objects_for_payment(partner, include_upcoming=False):
        """
        Get all debt objects for a partner ready to be included in a payment link.

        Args:
            partner: Partner instance
            include_upcoming: Whether to include upcoming debts (default False)

        Returns:
            List: List of all debt objects (Installment, Contribution, SocialSecurity, Penalty)
        """
        debts = PartnerDebtService.get_partner_overdue_debts(
            partner, include_upcoming=include_upcoming
        )
        return debts["all_debts"]
