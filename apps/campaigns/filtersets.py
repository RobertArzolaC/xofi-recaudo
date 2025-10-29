import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.campaigns import choices, models


class CampaignFilterSet(django_filters.FilterSet):
    """FilterSet for Campaign model with essential filtering options."""

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

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.CampaignStatus.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Active campaigns filter
    is_active = django_filters.BooleanFilter(
        method="filter_is_active",
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=[
                ("", _("All")),
                ("true", _("Active")),
                ("false", _("Inactive")),
            ],
        ),
        label=_("Active Status"),
    )

    # Payment link filter
    use_payment_link = django_filters.BooleanFilter(
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=[
                ("", _("All")),
                ("true", _("Yes")),
                ("false", _("No")),
            ],
        ),
        label=_("Use Payment Link"),
    )

    class Meta:
        model = models.Campaign
        fields = ["search", "status", "use_payment_link"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(description__icontains=value)
            )
        return queryset

    def filter_is_active(self, queryset, name, value):
        """Filter by active status."""
        if value is not None:
            if value:
                return queryset.filter(status=choices.CampaignStatus.ACTIVE)
            else:
                return queryset.exclude(status=choices.CampaignStatus.ACTIVE)
        return queryset


class GroupFilterSet(django_filters.FilterSet):
    """FilterSet for Group model with essential filtering options."""

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

    # Priority filter
    priority = django_filters.ChoiceFilter(
        choices=choices.GroupPriority.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All priorities"),
        label=_("Priority"),
    )

    # Partner count filter
    has_partners = django_filters.BooleanFilter(
        method="filter_has_partners",
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=[
                ("", _("All")),
                ("true", _("With Partners")),
                ("false", _("Without Partners")),
            ],
        ),
        label=_("Has Partners"),
    )

    class Meta:
        model = models.Group
        fields = ["search", "priority", "has_partners"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(description__icontains=value)
            )
        return queryset

    def filter_has_partners(self, queryset, name, value):
        """Filter groups by whether they have partners."""
        if value is not None:
            if value:
                return queryset.filter(partners__isnull=False).distinct()
            else:
                return queryset.filter(partners__isnull=True)
        return queryset
