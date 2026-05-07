import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core import choices as core_choices
from apps.partners import choices, models
from apps.customers import models as customer_models


class ApplicantFilterSet(django_filters.FilterSet):
    """FilterSet for Applicant model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name, document or email..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.ApplicantStatus.choices,
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Gender filter
    gender = django_filters.ChoiceFilter(
        choices=core_choices.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All genders"),
        label=_("Gender"),
    )

    # Agency filter
    agency = django_filters.ModelChoiceFilter(
        queryset=customer_models.Agency.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All agencies"),
        label=_("Agency"),
    )

    class Meta:
        model = models.Applicant
        fields = ["search", "status", "gender", "agency"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            query = Q()
            for term in value.split():
                query &= (
                    Q(first_name__icontains=term)
                    | Q(paternal_last_name__icontains=term)
                    | Q(maternal_last_name__icontains=term)
                    | Q(document_number__icontains=term)
                    | Q(email__icontains=term)
                    | Q(external_id__icontains=term)
                )
            return queryset.filter(query)
        return queryset


class PartnerFilterSet(django_filters.FilterSet):
    """FilterSet for Partner model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name, document or email..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.PartnerStatus.choices,
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Gender filter
    gender = django_filters.ChoiceFilter(
        choices=core_choices.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All genders"),
        label=_("Gender"),
    )

    # Agency filter
    agency = django_filters.ModelChoiceFilter(
        queryset=customer_models.Agency.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All agencies"),
        label=_("Agency"),
    )

    class Meta:
        model = models.Partner
        fields = ["search", "status", "gender", "agency"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            query = Q()
            for term in value.split():
                query &= (
                    Q(first_name__icontains=term)
                    | Q(paternal_last_name__icontains=term)
                    | Q(maternal_last_name__icontains=term)
                    | Q(document_number__icontains=term)
                    | Q(email__icontains=term)
                )
            return queryset.filter(query)
        return queryset


class ProspectFilterSet(django_filters.FilterSet):
    """FilterSet for Prospect model with essential filtering options."""

    # Search filter
    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name, document or email..."),
            }
        ),
        label=_("Search"),
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=choices.ProspectStatus.choices,
        widget=forms.Select(attrs={"class": "form-select", "data-control": "select2"}),
        empty_label=_("All statuses"),
        label=_("Status"),
    )

    # Source filter
    source = django_filters.CharFilter(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by source..."),
            }
        ),
        lookup_expr="icontains",
        label=_("Source"),
    )

    class Meta:
        model = models.Prospect
        fields = ["search", "status", "source"]

    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        if value:
            query = Q()
            for term in value.split():
                query &= (
                    Q(first_name__icontains=term)
                    | Q(last_name__icontains=term)
                    | Q(document_number__icontains=term)
                    | Q(email__icontains=term)
                    | Q(phone__icontains=term)
                )
            return queryset.filter(query)
        return queryset
