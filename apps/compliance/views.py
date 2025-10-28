import logging
from typing import Any, Dict

from constance import config
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.compliance import filtersets, forms, models
from apps.partners import mixins as partner_mixins

logger = logging.getLogger(__name__)


class ContributionListView(
    partner_mixins.PartnerAccessMixin, PermissionRequiredMixin, FilterView
):
    """List view for Contribution model with filtering."""

    model = models.Contribution
    filterset_class = filtersets.ContributionFilterSet
    template_name = "compliance/contribution/list.html"
    context_object_name = "contributions"
    permission_required = "compliance.view_contribution"
    paginate_by = config.ITEMS_PER_PAGE


class ContributionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Contribution model."""

    model = models.Contribution
    template_name = "compliance/contribution/detail.html"
    context_object_name = "contribution"
    permission_required = "compliance.view_contribution"

    def get_queryset(self) -> QuerySet[models.Contribution]:
        """Return queryset with related objects."""
        return models.Contribution.objects.select_related(
            "partner",
            "partner__country",
            "partner__region",
            "partner__subregion",
            "partner__city",
        ).prefetch_related("payments")


class ContributionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Contribution model."""

    model = models.Contribution
    form_class = forms.ContributionForm
    template_name = "compliance/contribution/form.html"
    permission_required = "compliance.add_contribution"
    success_url = reverse_lazy("apps.compliance:contribution-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Contribution")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set the created_by user before saving."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ContributionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Contribution model."""

    model = models.Contribution
    form_class = forms.ContributionForm
    template_name = "compliance/contribution/form.html"
    permission_required = "compliance.change_contribution"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.compliance:contribution-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Contribution')}: {self.object}"
        context["action"] = _("update")
        return context

    def form_valid(self, form):
        """Set the modified_by user before saving."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ContributionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Contribution model."""

    model = models.Contribution
    template_name = "compliance/contribution/confirm_delete.html"
    permission_required = "compliance.delete_contribution"
    success_url = reverse_lazy("apps.compliance:contribution-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Contribution')}: {self.object}"
        return context


# SocialSecurity Views
class SocialSecurityListView(
    partner_mixins.PartnerAccessMixin, PermissionRequiredMixin, FilterView
):
    """List view for SocialSecurity model with filtering."""

    model = models.SocialSecurity
    filterset_class = filtersets.SocialSecurityFilterSet
    template_name = "compliance/social_security/list.html"
    context_object_name = "social_securities"
    permission_required = "compliance.view_socialsecurity"
    paginate_by = config.ITEMS_PER_PAGE


class SocialSecurityDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for SocialSecurity model."""

    model = models.SocialSecurity
    template_name = "compliance/social_security/detail.html"
    context_object_name = "social_security"
    permission_required = "compliance.view_socialsecurity"

    def get_queryset(self) -> QuerySet[models.SocialSecurity]:
        """Return queryset with related objects."""
        return models.SocialSecurity.objects.select_related(
            "partner",
            "partner__country",
            "partner__region",
            "partner__subregion",
            "partner__city",
        ).prefetch_related("payments")


class SocialSecurityCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for SocialSecurity model."""

    model = models.SocialSecurity
    form_class = forms.SocialSecurityForm
    template_name = "compliance/social_security/form.html"
    permission_required = "compliance.add_socialsecurity"
    success_url = reverse_lazy("apps.compliance:social-security-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Social Security")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set the created_by user before saving."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class SocialSecurityUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for SocialSecurity model."""

    model = models.SocialSecurity
    form_class = forms.SocialSecurityForm
    template_name = "compliance/social_security/form.html"
    permission_required = "compliance.change_socialsecurity"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.compliance:social-security-detail",
            kwargs={"pk": self.object.pk},
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Social Security')}: {self.object}"
        context["action"] = _("update")
        return context

    def form_valid(self, form):
        """Set the modified_by user before saving."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class SocialSecurityDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for SocialSecurity model."""

    model = models.SocialSecurity
    template_name = "compliance/social_security/confirm_delete.html"
    permission_required = "compliance.delete_socialsecurity"
    success_url = reverse_lazy("apps.compliance:social-security-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Social Security')}: {self.object}"
        return context


# Penalty Views
class PenaltyListView(
    partner_mixins.PartnerAccessMixin, PermissionRequiredMixin, FilterView
):
    """List view for Penalty model with filtering."""

    model = models.Penalty
    filterset_class = filtersets.PenaltyFilterSet
    template_name = "compliance/penalty/list.html"
    context_object_name = "penalties"
    permission_required = "compliance.view_penalty"
    paginate_by = config.ITEMS_PER_PAGE


class PenaltyDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Penalty model."""

    model = models.Penalty
    template_name = "compliance/penalty/detail.html"
    context_object_name = "penalty"
    permission_required = "compliance.view_penalty"

    def get_queryset(self) -> QuerySet[models.Penalty]:
        """Return queryset with related objects."""
        return models.Penalty.objects.select_related(
            "partner",
            "partner__country",
            "partner__region",
            "partner__subregion",
            "partner__city",
        ).prefetch_related("payments")


class PenaltyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Penalty model."""

    model = models.Penalty
    form_class = forms.PenaltyForm
    template_name = "compliance/penalty/form.html"
    permission_required = "compliance.add_penalty"
    success_url = reverse_lazy("apps.compliance:penalty-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Penalty")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set the created_by user before saving."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PenaltyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Penalty model."""

    model = models.Penalty
    form_class = forms.PenaltyForm
    template_name = "compliance/penalty/form.html"
    permission_required = "compliance.change_penalty"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.compliance:penalty-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Penalty')}: {self.object}"
        context["action"] = _("update")
        return context

    def form_valid(self, form):
        """Set the modified_by user before saving."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class PenaltyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Penalty model."""

    model = models.Penalty
    template_name = "compliance/penalty/confirm_delete.html"
    permission_required = "compliance.delete_penalty"
    success_url = reverse_lazy("apps.compliance:penalty-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Penalty')}: {self.object}"
        return context
