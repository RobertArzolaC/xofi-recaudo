import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.support import choices, models


class TicketFilterSet(django_filters.FilterSet):
    """FilterSet for Ticket model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by subject, partner or ticket #..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.TicketStatus.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Priority filter
    priority = django_filters.ChoiceFilter(
        choices=choices.TicketPriority.choices,
        widget=forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
        empty_label=_("All priorities"),
        label=_("Priority"),
    )

    # Date range filter
    created_after = django_filters.DateFilter(
        field_name="created",
        lookup_expr="gte",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
        label=_("Created After"),
    )

    class Meta:
        model = models.Ticket
        fields = ["search", "status", "priority", "created_after"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            return queryset.filter(
                Q(subject__icontains=value)
                | Q(description__icontains=value)
                | Q(partner__first_name__icontains=value)
                | Q(partner__paternal_last_name__icontains=value)
                | Q(partner__document_number__icontains=value)
                | Q(pk__icontains=value)
            )
        return queryset
