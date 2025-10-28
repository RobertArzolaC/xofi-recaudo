import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.customers import models


class AccountFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(
        method="filter_by_name", label=_("Search")
    )
    is_active = django_filters.ChoiceFilter(
        field_name="user__is_active",
        empty_label=_("Is Active?"),
        label=_("Status"),
        choices=(
            (True, _("Active")),
            (False, _("Inactive")),
        ),
    )

    class Meta:
        model = models.Account
        fields = ["name_search", "is_active"]

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value)  # noqa
            | Q(user__last_name__icontains=value)  # noqa
            | Q(user__email__icontains=value)  # noqa
        )


class AgencyFilter(django_filters.FilterSet):
    """
    FilterSet for Agency model with name and active status filters.
    """

    search = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label=_("Search"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": _("Search by name..."),
            }
        ),
    )

    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label=_("Status"),
        widget=forms.Select(
            choices=[
                ("", _("All")),
                (True, _("Active")),
                (False, _("Inactive")),
            ],
            attrs={"class": "form-select form-select-sm"},
        ),
    )

    class Meta:
        model = models.Agency
        fields = ["search", "is_active"]
