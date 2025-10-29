from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.campaigns import choices
from apps.core import models as core_models


class Group(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a group of partners for campaigns."""

    partners = models.ManyToManyField(
        "partners.Partner",
        related_name="campaign_groups",
        verbose_name=_("Partners"),
        blank=True,
        help_text=_("Partners included in this group."),
    )
    priority = models.IntegerField(
        _("Priority"),
        choices=choices.GroupPriority.choices,
        default=choices.GroupPriority.MEDIUM,
        help_text=_("Priority level of the group."),
    )

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name

    @property
    def partner_count(self):
        """Return the number of partners in the group."""
        return self.partners.count()

    @property
    def total_outstanding_debt(self):
        """Return the total overdue debt of all partners in the group."""
        from decimal import Decimal

        from django.db.models import Sum
        from django.utils import timezone

        try:
            total_debt = Decimal("0.00")
            partners = self.partners.all()
            today = timezone.now().date()

            # Credit installments overdue
            from apps.credits.choices import InstallmentStatus
            from apps.credits.models import Installment

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

            # Compliance debts overdue
            from apps.compliance.choices import ComplianceStatus
            from apps.compliance.models import (
                Contribution,
                Penalty,
                SocialSecurity,
            )

            # Contributions overdue
            overdue_contributions = Contribution.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=[
                    ComplianceStatus.PENDING,
                    ComplianceStatus.OVERDUE,
                    ComplianceStatus.PARTIAL,
                ],
            )
            contribution_debt = overdue_contributions.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
            total_debt += contribution_debt

            # Social Security overdue
            overdue_social_security = SocialSecurity.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=[
                    ComplianceStatus.PENDING,
                    ComplianceStatus.OVERDUE,
                    ComplianceStatus.PARTIAL,
                ],
            )
            social_security_debt = overdue_social_security.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
            total_debt += social_security_debt

            # Penalties overdue
            overdue_penalties = Penalty.objects.filter(
                partner__in=partners,
                due_date__lt=today,
                status__in=[
                    ComplianceStatus.PENDING,
                    ComplianceStatus.OVERDUE,
                    ComplianceStatus.PARTIAL,
                ],
            )
            penalty_debt = overdue_penalties.aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")
            total_debt += penalty_debt

            return total_debt

        except Exception:
            return Decimal("0.00")

    @property
    def overdue_obligations_count(self):
        """Return the total number of overdue obligations for partners in the group."""
        from django.utils import timezone

        try:
            partners = self.partners.all()
            today = timezone.now().date()
            total_count = 0

            # Overdue credit installments
            from apps.credits.choices import InstallmentStatus
            from apps.credits.models import Installment

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

            # Overdue compliance obligations
            from apps.compliance.choices import ComplianceStatus
            from apps.compliance.models import (
                Contribution,
                Penalty,
                SocialSecurity,
            )

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

    def get_debt_summary(self):
        """Return a detailed summary of overdue debts for partners in the group."""
        from decimal import Decimal

        from django.db.models import Count, Sum
        from django.utils import timezone

        try:
            partners = self.partners.all()
            today = timezone.now().date()
            total_debt = Decimal("0.00")

            # Credit installments overdue
            from apps.credits.choices import InstallmentStatus
            from apps.credits.models import Installment

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

            # Compliance debts overdue
            from apps.compliance.choices import ComplianceStatus
            from apps.compliance.models import (
                Contribution,
                Penalty,
                SocialSecurity,
            )

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

    def get_partners_debt_detail(self):
        """Return detailed debt information for each partner in the group."""
        from decimal import Decimal

        from django.db.models import Sum
        from django.utils import timezone

        try:
            partners_detail = []
            today = timezone.now().date()

            for partner in self.partners.all():
                partner_debt = {
                    "partner": partner,
                    "total_debt": Decimal("0.00"),
                    "credit_debt": Decimal("0.00"),
                    "contribution_debt": Decimal("0.00"),
                    "social_security_debt": Decimal("0.00"),
                    "penalty_debt": Decimal("0.00"),
                }

                # Credit installments overdue
                from apps.credits.choices import InstallmentStatus
                from apps.credits.models import Installment

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
                partner_debt["credit_debt"] = credit_debt
                partner_debt["total_debt"] += credit_debt

                # Compliance debts overdue
                from apps.compliance.choices import ComplianceStatus
                from apps.compliance.models import (
                    Contribution,
                    Penalty,
                    SocialSecurity,
                )

                overdue_status = [
                    ComplianceStatus.PENDING,
                    ComplianceStatus.OVERDUE,
                    ComplianceStatus.PARTIAL,
                ]

                # Contributions
                contribution_debt = Contribution.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                partner_debt["contribution_debt"] = contribution_debt
                partner_debt["total_debt"] += contribution_debt

                # Social Security
                social_security_debt = SocialSecurity.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                partner_debt["social_security_debt"] = social_security_debt
                partner_debt["total_debt"] += social_security_debt

                # Penalties
                penalty_debt = Penalty.objects.filter(
                    partner=partner,
                    due_date__lt=today,
                    status__in=overdue_status,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                partner_debt["penalty_debt"] = penalty_debt
                partner_debt["total_debt"] += penalty_debt

                # Only include partners with debt
                if partner_debt["total_debt"] > 0:
                    partners_detail.append(partner_debt)

            return partners_detail

        except Exception:
            return []


class Campaign(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent collection campaigns."""

    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="campaigns",
        verbose_name=_("Group"),
        null=True,
        blank=True,
        help_text=_("Group associated with this campaign."),
    )
    start_date = models.DateField(
        _("Start Date"),
        null=True,
        blank=True,
        help_text=_("Date when the campaign starts."),
    )
    end_date = models.DateField(
        _("End Date"),
        null=True,
        blank=True,
        help_text=_("Date when the campaign ends."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.CampaignStatus.choices,
        default=choices.CampaignStatus.DRAFT,
        help_text=_("Current status of the campaign."),
    )
    target_amount = models.DecimalField(
        _("Target Amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Target collection amount for the campaign."),
    )

    # Execution schedule
    execution_time = models.TimeField(
        _("Execution Time"),
        null=True,
        blank=True,
        help_text=_(
            "Time of day when the campaign notifications will be sent."
        ),
    )

    # Notification configuration
    notify_3_days_before = models.BooleanField(
        _("Notify 3 Days Before"),
        default=False,
        help_text=_("Send notification 3 days before due date."),
    )
    notify_on_due_date = models.BooleanField(
        _("Notify on Due Date"),
        default=True,
        help_text=_("Send notification on the due date."),
    )
    notify_3_days_after = models.BooleanField(
        _("Notify 3 Days After"),
        default=False,
        help_text=_("Send notification 3 days after due date."),
    )
    notify_7_days_after = models.BooleanField(
        _("Notify 7 Days After"),
        default=False,
        help_text=_("Send notification 7 days after due date."),
    )

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Check if campaign is currently active."""
        return self.status == choices.CampaignStatus.ACTIVE
