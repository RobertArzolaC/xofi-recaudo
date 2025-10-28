"""
FilterSets for team models.
"""

import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.customers import models as customer_models
from apps.team import choices, models


class AreaFilterSet(django_filters.FilterSet):
    """FilterSet for Area model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name or description..."),
            }
        ),
        label=_("Search"),
    )

    class Meta:
        model = models.Area
        fields = ["search"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(description__icontains=value)
            )
        return queryset


class PositionFilterSet(django_filters.FilterSet):
    """FilterSet for Position model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name or description..."),
            }
        ),
        label=_("Search"),
    )

    # Area filter
    area = django_filters.ModelChoiceFilter(
        queryset=models.Area.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All areas"),
        label=_("Area"),
    )

    class Meta:
        model = models.Position
        fields = ["search", "area"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(description__icontains=value)
            )
        return queryset


class EmployeeFilterSet(django_filters.FilterSet):
    """FilterSet for Employee model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name, email or phone..."),
            }
        ),
        label=_("Search"),
    )

    # Position filter
    position = django_filters.ModelChoiceFilter(
        queryset=models.Position.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All positions"),
        label=_("Position"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.EmployeeStatus.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Agency filter
    agency = django_filters.ModelChoiceFilter(
        queryset=customer_models.Agency.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All agencies"),
        label=_("Agency"),
    )

    class Meta:
        model = models.Employee
        fields = ["search", "position", "status", "agency"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(first_name__icontains=value)
                | Q(paternal_last_name__icontains=value)
                | Q(maternal_last_name__icontains=value)
                | Q(email__icontains=value)
                | Q(phone__icontains=value)
                | Q(user__username__icontains=value)
                | Q(user__email__icontains=value)
            )
        return queryset

    def filter_area(self, queryset, name, value):
        """Filter employees by area through position relationship."""
        if value:
            return queryset.filter(position__area=value)
        return queryset
