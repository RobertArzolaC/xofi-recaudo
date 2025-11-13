import django_filters
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.reports import choices
from apps.reports.models import Report, ReportType


class ReportFilter(django_filters.FilterSet):
    """
    FilterSet for Report model with search and filtering capabilities.
    """

    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by title or description"),
            }
        ),
        label=_("Search"),
    )

    report_type = django_filters.ModelChoiceFilter(
        queryset=ReportType.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Report Type"),
        empty_label=_("All Types"),
    )

    status = django_filters.ChoiceFilter(
        choices=[("", _("All Status"))] + choices.ReportStatus.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Status"),
        empty_label=None,
    )

    class Meta:
        model = Report
        fields = ["search", "report_type", "status"]

    def filter_search(self, queryset, name, value):
        """
        Custom search filter to search in title and description.
        """
        if value:
            return queryset.filter(
                models.Q(title__icontains=value)
                | models.Q(description__icontains=value)
            )
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values to empty
        for field in self.form.fields.values():
            if hasattr(field, "empty_label"):
                field.empty_label = None
