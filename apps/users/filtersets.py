import django_filters
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Filter for User model with search and status filters."""

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        help_text=_("Search by name or email"),
    )

    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label=_("Active Status"),
        help_text=_("Filter by active/inactive users"),
    )

    groups = django_filters.ModelChoiceFilter(
        field_name="groups",
        queryset=Group.objects.all().order_by("name"),
        label=_("Role"),
        help_text=_("Filter by assigned role"),
    )

    class Meta:
        model = User
        fields = ["search", "is_active", "groups"]

    def filter_search(
        self, queryset: QuerySet[User], name: str, value: str
    ) -> QuerySet[User]:
        """
        Filter users by search term in first name, last name, or email.

        Args:
            queryset: The base queryset to filter
            name: The filter field name
            value: The search term

        Returns:
            Filtered queryset matching the search term
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )
