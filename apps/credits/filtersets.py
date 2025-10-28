import django_filters
from django.utils.translation import gettext_lazy as _

from apps.credits import models


class ProductTypeFilter(django_filters.FilterSet):
    """Filter for ProductType model."""

    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label=_("Name"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name..."),
            }
        ),
    )
    description = django_filters.CharFilter(
        lookup_expr="icontains",
        label=_("Description"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by description..."),
            }
        ),
    )
    is_active = django_filters.BooleanFilter(
        label=_("Is Active"),
        widget=django_filters.widgets.forms.Select(
            choices=[
                (None, _("All")),
                (True, _("Active")),
                (False, _("Inactive")),
            ],
            attrs={"class": "form-select"},
        ),
    )

    class Meta:
        model = models.ProductType
        fields = ["name", "description", "is_active"]


class ProductFilter(django_filters.FilterSet):
    """Filter for Product model."""

    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label=_("Name"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by name..."),
            }
        ),
    )
    product_type = django_filters.ModelChoiceFilter(
        queryset=models.ProductType.objects.filter(is_active=True),
        label=_("Product Type"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )
    is_active = django_filters.BooleanFilter(
        label=_("Is Active"),
        widget=django_filters.widgets.forms.Select(
            choices=[
                (None, _("All")),
                (True, _("Active")),
                (False, _("Inactive")),
            ],
            attrs={"class": "form-select"},
        ),
    )

    class Meta:
        model = models.Product
        fields = ["name", "product_type", "is_active"]


class CreditFilter(django_filters.FilterSet):
    """Filter for Credit model."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name, email, phone..."),
            }
        ),
    )
    product = django_filters.ModelChoiceFilter(
        queryset=models.Product.objects.filter(is_active=True),
        label=_("Product"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
    )
    status = django_filters.ChoiceFilter(
        choices=models.Credit._meta.get_field("status").choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = models.Credit
        fields = ["search", "partner", "product", "status"]

    def filter_search(self, queryset, name: str, value):
        """Filter credits by partner fields."""
        if value:
            return queryset.filter(
                models.Q(partner__first_name__icontains=value)
                | models.Q(partner__paternal_last_name__icontains=value)
                | models.Q(partner__maternal_last_name__icontains=value)
                | models.Q(partner__email__icontains=value)
                | models.Q(partner__phone__icontains=value)
                | models.Q(partner__document_number__icontains=value)
            )
        return queryset


class CreditApplicationFilter(django_filters.FilterSet):
    """Filter for CreditApplication model."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name, email, phone..."),
            }
        ),
    )
    product = django_filters.ModelChoiceFilter(
        queryset=models.Product.objects.filter(is_active=True),
        label=_("Product"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )
    status = django_filters.ChoiceFilter(
        choices=models.CreditApplication._meta.get_field("status").choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = models.CreditApplication
        fields = ["search", "product", "status"]

    def filter_search(self, queryset, name: str, value):
        """Filter credit applications by partner fields."""
        if value:
            return queryset.filter(
                models.Q(partner__first_name__icontains=value)
                | models.Q(partner__paternal_last_name__icontains=value)
                | models.Q(partner__maternal_last_name__icontains=value)
                | models.Q(partner__email__icontains=value)
                | models.Q(partner__phone__icontains=value)
                | models.Q(partner__document_number__icontains=value)
            )
        return queryset


class CreditRescheduleRequestFilter(django_filters.FilterSet):
    """Filter for CreditRescheduleRequest model."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name, credit..."),
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        choices=models.CreditRescheduleRequest._meta.get_field("status").choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )
    credit__product = django_filters.ModelChoiceFilter(
        queryset=models.Product.objects.filter(is_active=True),
        label=_("Product"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
    )

    class Meta:
        model = models.CreditRescheduleRequest
        fields = ["search", "status", "credit__product"]

    def filter_search(self, queryset, name: str, value):
        """Filter reschedule requests by partner and credit fields."""
        if value:
            return queryset.filter(
                models.Q(credit__partner__first_name__icontains=value)
                | models.Q(credit__partner__paternal_last_name__icontains=value)
                | models.Q(credit__partner__maternal_last_name__icontains=value)
                | models.Q(credit__partner__email__icontains=value)
                | models.Q(credit__partner__phone__icontains=value)
                | models.Q(credit__partner__document_number__icontains=value)
                | models.Q(credit__product__name__icontains=value)
                | models.Q(reason__icontains=value)
            )
        return queryset


class CreditRefinanceRequestFilter(django_filters.FilterSet):
    """Filter for CreditRefinanceRequest model."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name, credit..."),
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        choices=models.CreditRefinanceRequest._meta.get_field("status").choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )
    credit__product = django_filters.ModelChoiceFilter(
        queryset=models.Product.objects.filter(is_active=True),
        label=_("Product"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(
            attrs={"class": "form-select", "data-control": "select2"}
        ),
    )

    class Meta:
        model = models.CreditRefinanceRequest
        fields = ["search", "status", "credit__product"]

    def filter_search(self, queryset, name: str, value):
        """Filter refinance requests by partner and credit fields."""
        if value:
            return queryset.filter(
                models.Q(credit__partner__first_name__icontains=value)
                | models.Q(credit__partner__paternal_last_name__icontains=value)
                | models.Q(credit__partner__maternal_last_name__icontains=value)
                | models.Q(credit__partner__email__icontains=value)
                | models.Q(credit__partner__phone__icontains=value)
                | models.Q(credit__partner__document_number__icontains=value)
                | models.Q(credit__product__name__icontains=value)
                | models.Q(reason__icontains=value)
            )
        return queryset


class CreditDisbursementFilter(django_filters.FilterSet):
    """Filter for CreditDisbursement model."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search by partner name, credit..."),
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        choices=models.CreditDisbursement._meta.get_field("status").choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )
    disbursement_method = django_filters.ChoiceFilter(
        choices=models.CreditDisbursement._meta.get_field(
            "disbursement_method"
        ).choices,
        label=_("Disbursement Method"),
        empty_label=_("All"),
        widget=django_filters.widgets.forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = models.CreditDisbursement
        fields = ["search", "status", "disbursement_method"]

    def filter_search(self, queryset, name: str, value):
        """Filter disbursements by partner and credit fields."""
        if value:
            return queryset.filter(
                models.Q(credit__partner__first_name__icontains=value)
                | models.Q(credit__partner__paternal_last_name__icontains=value)
                | models.Q(credit__partner__maternal_last_name__icontains=value)
                | models.Q(credit__partner__email__icontains=value)
                | models.Q(credit__partner__phone__icontains=value)
                | models.Q(credit__partner__document_number__icontains=value)
                | models.Q(credit__product__name__icontains=value)
                | models.Q(reference_number__icontains=value)
            )
        return queryset
