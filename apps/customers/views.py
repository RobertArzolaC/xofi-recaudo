from typing import Any, Dict

from constance import config
from dal import autocomplete
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.core import mixins as core_mixins
from apps.customers import filtersets, forms, models


class AccountListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Account
    permission_required = "customers.view_account"
    filterset_class = filtersets.AccountFilter
    template_name = "customers/account/list.html"
    context_object_name = "accounts"
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = config
        context["entity"] = _("Account")
        context["entity_plural"] = _("Accounts")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy(
            "apps.customers:account_create"
        )

        return context


class AccountCreateView(
    PermissionRequiredMixin, FormView, LoginRequiredMixin, SuccessMessageMixin
):
    form_class = forms.AccountCreationForm
    permission_required = "customers.add_account"
    template_name = "customers/account/form.html"
    success_message = _("Account created successfully")
    success_url = reverse_lazy("apps.customers:account_list")

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.customers:account_list")
        return context


class AccountUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = models.Account
    context_object_name = "account"
    form_class = forms.AccountUpdateForm
    template_name = "customers/account/form.html"
    permission_required = "customers.change_account"
    success_message = _("Account updated successfully")
    success_url = reverse_lazy("apps.customers:account_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.customers:account_list")
        return context


class AccountDeleteView(core_mixins.AjaxDeleteViewMixin):
    model = models.Account


class CompanyDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """Detail view for Company model."""

    model = models.Company
    template_name = "customers/company/detail.html"
    context_object_name = "company"
    permission_required = "customers.view_company"

    def get_queryset(self) -> QuerySet[models.Company]:
        """Return queryset with related objects."""
        return models.Company.objects.select_related(
            "country",
            "region",
            "subregion",
            "city",
            "created_by",
            "modified_by",
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add Constance values to context."""
        context = super().get_context_data(**kwargs)
        context["compliance_settings"] = {
            "contribution_amount": config.CONTRIBUTION_AMOUNT,
            "social_security_amount": config.SOCIAL_SECURITY_AMOUNT,
            "contribution_due_day": config.CONTRIBUTION_DUE_DAY,
            "social_security_due_day": config.SOCIAL_SECURITY_DUE_DAY,
        }
        return context


class CompanyUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Company model."""

    model = models.Company
    form_class = forms.CompanyForm
    template_name = "customers/company/form.html"
    permission_required = "customers.change_company"

    def form_valid(self, form: forms.CompanyForm) -> HttpResponse:
        """Set the updated_by field before saving."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.customers:company-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Company: {self.object.name}"
        context["action"] = "update"
        return context


class AgencyListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Agency model with filtering."""

    model = models.Agency
    template_name = "customers/agency/list.html"
    context_object_name = "agencies"
    permission_required = "customers.view_agency"
    filterset_class = filtersets.AgencyFilter
    paginate_by = 5

    def get_queryset(self) -> QuerySet[models.Agency]:
        """Return queryset with optimized queries."""
        return models.Agency.objects.select_related(
            "created_by",
            "modified_by",
        ).order_by("name")


class AgencyDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Agency model."""

    model = models.Agency
    template_name = "customers/agency/detail.html"
    context_object_name = "agency"
    permission_required = "customers.view_agency"

    def get_queryset(self) -> QuerySet[models.Agency]:
        """Return queryset with related objects."""
        return models.Agency.objects.select_related(
            "country",
            "region",
            "subregion",
            "city",
            "created_by",
            "modified_by",
        )


class AgencyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Agency model."""

    model = models.Agency
    form_class = forms.AgencyForm
    template_name = "customers/agency/form.html"
    permission_required = "customers.add_agency"

    def form_valid(self, form: forms.AgencyForm) -> HttpResponse:
        """Set the created_by field before saving."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.customers:agency-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Agency"
        context["action"] = "create"
        return context


class AgencyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Agency model."""

    model = models.Agency
    form_class = forms.AgencyForm
    template_name = "customers/agency/form.html"
    permission_required = "customers.change_agency"

    def form_valid(self, form: forms.AgencyForm) -> HttpResponse:
        """Set the modified_by field before saving."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.customers:agency-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Agency: {self.object.name}"
        context["action"] = "update"
        return context


class AgencyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Agency model."""

    model = models.Agency
    template_name = "customers/agency/confirm_delete.html"
    context_object_name = "agency"
    permission_required = "customers.delete_agency"
    success_url = reverse_lazy("apps.customers:agency-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete Agency: {self.object.name}"
        return context


class AgencyAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Agency model."""

    def get_queryset(self):
        """Return filtered queryset for autocomplete."""
        if not self.request.user.is_authenticated:
            return models.Agency.objects.none()

        qs = models.Agency.objects.filter(is_active=True)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")
