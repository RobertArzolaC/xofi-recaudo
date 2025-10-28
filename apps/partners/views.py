import logging
from typing import Any, Dict

from constance import config
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.partners import filtersets, forms, models

logger = logging.getLogger(__name__)


class ApplicantListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """List view for Applicant model with filtering."""

    model = models.Applicant
    filterset_class = filtersets.ApplicantFilterSet
    template_name = "partners/applicant/list.html"
    context_object_name = "applicants"
    permission_required = "partners.view_applicant"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Applicant]:
        """Return filtered and ordered queryset."""
        return models.Applicant.objects.select_related(
            "country", "region", "subregion", "city"
        ).order_by("-created")


class ApplicantDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """Detail view for Applicant model."""

    model = models.Applicant
    template_name = "partners/applicant/detail.html"
    context_object_name = "applicant"
    permission_required = "partners.view_applicant"

    def get_queryset(self) -> QuerySet[models.Applicant]:
        """Return queryset with related objects."""
        return models.Applicant.objects.select_related(
            "country", "region", "subregion", "city"
        )


class ApplicantCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """Create view for Applicant model."""

    model = models.Applicant
    form_class = forms.ApplicantForm
    template_name = "partners/applicant/form.html"
    permission_required = "partners.add_applicant"
    success_url = reverse_lazy("apps.partners:applicant-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Applicant"
        context["action"] = "create"
        return context


class ApplicantUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Applicant model."""

    model = models.Applicant
    form_class = forms.ApplicantForm
    template_name = "partners/applicant/form.html"
    permission_required = "partners.change_applicant"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.partners:applicant-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Applicant"
        context["action"] = _("update")
        return context


class ApplicantDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete view for Applicant model."""

    model = models.Applicant
    template_name = "partners/applicant/confirm_delete.html"
    permission_required = "partners.delete_applicant"
    success_url = reverse_lazy("apps.partners:applicant-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete Applicant: {self.object.full_name}"
        return context


class PartnerListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Partner model with filtering."""

    model = models.Partner
    filterset_class = filtersets.PartnerFilterSet
    template_name = "partners/partner/list.html"
    context_object_name = "partners"
    permission_required = "partners.view_partner"
    paginate_by = paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Partner]:
        """Return filtered and ordered queryset."""
        return models.Partner.objects.select_related(
            "country", "region", "subregion", "city"
        ).order_by("-created")


class PartnerDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """Detail view for Partner model."""

    model = models.Partner
    template_name = "partners/partner/detail.html"
    context_object_name = "partner"
    permission_required = "partners.view_partner"

    def get_queryset(self) -> QuerySet[models.Partner]:
        """Return queryset with related objects."""
        return models.Partner.objects.select_related(
            "country", "region", "subregion", "city"
        )


class PartnerCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """Create view for Partner model."""

    model = models.Partner
    form_class = forms.PartnerForm
    template_name = "partners/partner/form.html"
    permission_required = "partners.add_partner"
    success_url = reverse_lazy("apps.partners:partner-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Partner"
        context["action"] = "create"
        return context


class PartnerUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Partner model."""

    model = models.Partner
    form_class = forms.PartnerForm
    template_name = "partners/partner/form.html"
    permission_required = "partners.change_partner"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.partners:partner-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Partner: {self.object.full_name}"
        context["action"] = "update"
        return context

    def form_valid(self, form):
        """Update user tracking fields."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class PartnerEmploymentUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Partner employment information."""

    model = models.Partner
    template_name = "partners/partner/employment_form.html"
    permission_required = "partners.change_partner"

    def get_employment_info(self):
        """Get or create employment info for the partner."""
        try:
            return self.object.employment_info
        except models.PartnerEmploymentInfo.DoesNotExist:
            return models.PartnerEmploymentInfo(partner=self.object)

    def get_form(self, form_class=None):
        """Return employment form instance."""
        employment_info = self.get_employment_info()
        return forms.PartnerEmploymentInfoForm(
            data=self.request.POST or None, instance=employment_info
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Employment Information: {self.object.full_name}"
        context["employment_form"] = self.get_form()
        context["partner"] = self.object
        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission."""
        self.object = self.get_object()
        employment_form = self.get_form()

        if employment_form.is_valid():
            employment_info = employment_form.save(commit=False)
            employment_info.partner = self.object
            if not employment_info.pk:
                employment_info.created_by = request.user
            employment_info.modified_by = request.user
            employment_info.save()

            return self.form_valid(employment_form)
        else:
            return self.form_invalid(employment_form)

    def form_valid(self, form):
        """Redirect to partner detail on success."""
        return redirect(
            reverse_lazy(
                "apps.partners:partner-detail", kwargs={"pk": self.object.pk}
            )
        )

    def form_invalid(self, form):
        """Return to form with errors."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self) -> str:
        """Return success URL pointing to partner detail view."""
        return reverse_lazy(
            "apps.partners:partner-detail", kwargs={"pk": self.object.pk}
        )


class PartnerDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete view for Partner model."""

    model = models.Partner
    template_name = "partners/partner/confirm_delete.html"
    permission_required = "partners.delete_partner"
    success_url = reverse_lazy("apps.partners:partner-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete Partner: {self.object.full_name}"
        return context


class ProspectListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Prospect model with filtering."""

    model = models.Prospect
    filterset_class = filtersets.ProspectFilterSet
    template_name = "partners/prospect/list.html"
    context_object_name = "prospects"
    permission_required = "partners.view_prospect"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Prospect]:
        """Return filtered and ordered queryset."""
        return models.Prospect.objects.select_related("assigned_to").order_by(
            "-created"
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Prospects")
        return context


class ProspectDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """Detail view for Prospect model."""

    model = models.Prospect
    template_name = "partners/prospect/detail.html"
    context_object_name = "prospect"
    permission_required = "partners.view_prospect"

    def get_queryset(self) -> QuerySet[models.Prospect]:
        """Return queryset with related objects."""
        return models.Prospect.objects.select_related("assigned_to")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Prospect: {self.object.full_name}"
        return context


class ProspectUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Prospect model."""

    model = models.Prospect
    form_class = forms.ProspectForm
    template_name = "partners/prospect/form.html"
    permission_required = "partners.change_prospect"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.partners:prospect-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Prospect: {self.object.full_name}"
        context["action"] = "update"
        return context

    def form_valid(self, form):
        """Update user tracking fields."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)
