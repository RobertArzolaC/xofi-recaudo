import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.partners.models import Partner
from apps.payments import choices, models


class PaymentFilter(django_filters.FilterSet):
    """FilterSet for Payment model."""

    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _(
                    "Search by payment number, partner name, or email..."
                ),
            }
        ),
        label=_("Search"),
    )
    partner = django_filters.ModelChoiceFilter(
        queryset=Partner.objects.all(),
        empty_label=_("All Partners"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "data-control": "select2",
            }
        ),
        label=_("Partner"),
    )
    concept = django_filters.ChoiceFilter(
        choices=choices.PaymentConcept.choices,
        empty_label=_("All Concepts"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Concept"),
    )
    status = django_filters.ChoiceFilter(
        choices=choices.PaymentStatus.choices,
        empty_label=_("All Statuses"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Status"),
    )

    class Meta:
        model = models.Payment
        fields = []

    def __init__(self, *args, **kwargs):
        """Initialize filter with optimized querysets."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.filters["partner"].queryset = Partner.objects.order_by(
            "first_name"
        )

    def filter_search(self, queryset, name, value):
        """Filter by search term across multiple fields."""
        if value:
            return queryset.filter(
                Q(payment_number__icontains=value)
                | Q(partner__first_name__icontains=value)
                | Q(partner__email__icontains=value)
                | Q(reference_number__icontains=value)
                | Q(notes__icontains=value)
            )
        return queryset


class MagicPaymentLinkFilter(django_filters.FilterSet):
    """FilterSet for MagicPaymentLink model."""

    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner, document or title..."),
            }
        ),
        label=_("Search"),
    )
    status = django_filters.ChoiceFilter(
        choices=choices.MagicLinkStatus.choices,
        empty_label=_("All statuses"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Status"),
    )
    document = django_filters.CharFilter(
        field_name="partner__document_number",
        lookup_expr="icontains",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Document number"),
            }
        ),
        label=_("Document"),
    )
    partner = django_filters.ModelChoiceFilter(
        queryset=Partner.objects.all(),
        empty_label=_("All Partners"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "data-control": "select2",
            }
        ),
        label=_("Partner"),
    )

    class Meta:
        model = models.MagicPaymentLink
        fields = []

    def __init__(self, *args, **kwargs):
        """Initialize filter with optimized querysets."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.filters["partner"].queryset = Partner.objects.order_by(
            "first_name"
        )

    def filter_search(self, queryset, name, value):
        """Filter by search term across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value)
                | Q(description__icontains=value)
                | Q(partner__first_name__icontains=value)
                | Q(partner__last_name__icontains=value)
                | Q(partner__document_number__icontains=value)
                | Q(token__icontains=value)
            )
        return queryset


class PaymentReceiptFilter(django_filters.FilterSet):
    """FilterSet for PaymentReceipt model."""

    search = django_filters.CharFilter(
        method="filter_search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _(
                    "Search by partner name, document number, or notes..."
                ),
            }
        ),
        label=_("Search"),
    )
    partner = django_filters.ModelChoiceFilter(
        queryset=Partner.objects.all(),
        empty_label=_("All Partners"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "data-control": "select2",
            }
        ),
        label=_("Partner"),
    )
    status = django_filters.ChoiceFilter(
        choices=choices.ReceiptStatus.choices,
        empty_label=_("All Statuses"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Status"),
    )

    class Meta:
        model = models.PaymentReceipt
        fields = []

    def __init__(self, *args, **kwargs):
        """Initialize filter with optimized querysets."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.filters["partner"].queryset = Partner.objects.order_by(
            "first_name"
        )

    def filter_search(self, queryset, name, value):
        """Filter by search term across multiple fields."""
        if value:
            return queryset.filter(
                Q(partner__first_name__icontains=value)
                | Q(partner__last_name__icontains=value)
                | Q(partner__document_number__icontains=value)
                | Q(notes__icontains=value)
                | Q(validation_notes__icontains=value)
            )
        return queryset
