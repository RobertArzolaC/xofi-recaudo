import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.compliance import choices, models


class ContributionFilterSet(django_filters.FilterSet):
    """FilterSet for Contribution model with essential filtering options."""

    # Search filter for partner name and reference number
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name or reference..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.ComplianceStatus.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Year filter
    period_year = django_filters.NumberFilter(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Year"),
                "min": "2020",
                "max": "2030",
            }
        ),
        label=_("Period Year"),
    )

    # Month filter
    period_month = django_filters.ChoiceFilter(
        choices=[
            (1, _("January")),
            (2, _("February")),
            (3, _("March")),
            (4, _("April")),
            (5, _("May")),
            (6, _("June")),
            (7, _("July")),
            (8, _("August")),
            (9, _("September")),
            (10, _("October")),
            (11, _("November")),
            (12, _("December")),
        ],
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All months"),
        label=_("Period Month"),
    )

    class Meta:
        model = models.Contribution
        fields = ["search", "status", "period_year", "period_month"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across partner name and reference fields."""
        if value:
            return queryset.filter(
                Q(partner__first_name__icontains=value)
                | Q(partner__paternal_last_name__icontains=value)
                | Q(partner__maternal_last_name__icontains=value)
                | Q(reference_number__icontains=value)
            )
        return queryset


class SocialSecurityFilterSet(django_filters.FilterSet):
    """FilterSet for SocialSecurity model with essential filtering options."""

    # Search filter for partner name and reference number
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name or reference..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.ComplianceStatus.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Year filter
    period_year = django_filters.NumberFilter(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Year"),
                "min": "2020",
                "max": "2030",
            }
        ),
        label=_("Period Year"),
    )

    # Month filter
    period_month = django_filters.ChoiceFilter(
        choices=[
            (1, _("January")),
            (2, _("February")),
            (3, _("March")),
            (4, _("April")),
            (5, _("May")),
            (6, _("June")),
            (7, _("July")),
            (8, _("August")),
            (9, _("September")),
            (10, _("October")),
            (11, _("November")),
            (12, _("December")),
        ],
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All months"),
        label=_("Period Month"),
    )

    class Meta:
        model = models.SocialSecurity
        fields = ["search", "status", "period_year", "period_month"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across partner name and reference fields."""
        if value:
            return queryset.filter(
                Q(partner__first_name__icontains=value)
                | Q(partner__paternal_last_name__icontains=value)
                | Q(partner__maternal_last_name__icontains=value)
                | Q(reference_number__icontains=value)
            )
        return queryset


class PenaltyFilterSet(django_filters.FilterSet):
    """FilterSet for Penalty model with essential filtering options."""

    # Search filter for partner name and reference number
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name or reference..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.ComplianceStatus.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Penalty type filter
    penalty_type = django_filters.ChoiceFilter(
        choices=choices.PenaltyType.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All penalty types"),
        label=_("Penalty Type"),
    )

    # Issue date filter (year)
    issue_year = django_filters.NumberFilter(
        field_name="issue_date__year",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Year"),
                "min": "2020",
                "max": "2030",
            }
        ),
        label=_("Issue Year"),
    )

    class Meta:
        model = models.Penalty
        fields = ["search", "status", "penalty_type", "issue_year"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across partner name and reference fields."""
        if value:
            return queryset.filter(
                Q(partner__first_name__icontains=value)
                | Q(partner__paternal_last_name__icontains=value)
                | Q(partner__maternal_last_name__icontains=value)
                | Q(reference_number__icontains=value)
                | Q(description__icontains=value)
            )
        return queryset