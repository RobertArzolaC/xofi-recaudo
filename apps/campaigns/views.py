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
    View,
)
from django_filters.views import FilterView

from apps.campaigns import filtersets, forms, models

logger = logging.getLogger(__name__)


# Campaign Views
class CampaignListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Campaign model with filtering."""

    model = models.Campaign
    filterset_class = filtersets.CampaignFilterSet
    template_name = "campaigns/campaign/list.html"
    context_object_name = "campaigns"
    permission_required = "campaigns.view_campaign"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Campaign]:
        """Return filtered and ordered queryset."""
        return models.Campaign.objects.select_related("group").order_by(
            "-created"
        )


class CampaignDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """Detail view for Campaign model."""

    model = models.Campaign
    template_name = "campaigns/campaign/detail.html"
    context_object_name = "campaign"
    permission_required = "campaigns.view_campaign"

    def get_queryset(self) -> QuerySet[models.Campaign]:
        """Return queryset with related objects."""
        return models.Campaign.objects.select_related("group").prefetch_related(
            "group__partners"
        )


class CampaignCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """Create view for Campaign model."""

    model = models.Campaign
    form_class = forms.CampaignForm
    template_name = "campaigns/campaign/form.html"
    permission_required = "campaigns.add_campaign"
    success_url = reverse_lazy("apps.campaigns:campaign-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Campaign")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set user tracking fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CampaignUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update view for Campaign model."""

    model = models.Campaign
    form_class = forms.CampaignForm
    template_name = "campaigns/campaign/form.html"
    permission_required = "campaigns.change_campaign"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.campaigns:campaign-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Campaign')}: {self.object.name}"
        context["action"] = "update"
        return context

    def form_valid(self, form):
        """Update user tracking fields."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CampaignDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete view for Campaign model."""

    model = models.Campaign
    template_name = "campaigns/campaign/confirm_delete.html"
    permission_required = "campaigns.delete_campaign"
    success_url = reverse_lazy("apps.campaigns:campaign-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Campaign')}: {self.object.name}"
        return context


# Group Views
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Group model with filtering."""

    model = models.Group
    filterset_class = filtersets.GroupFilterSet
    template_name = "campaigns/group/list.html"
    context_object_name = "groups"
    permission_required = "campaigns.view_group"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Group]:
        """Return filtered and ordered queryset."""
        return models.Group.objects.prefetch_related("partners").order_by(
            "-created"
        )


class GroupDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Group model."""

    model = models.Group
    template_name = "campaigns/group/detail.html"
    context_object_name = "group"
    permission_required = "campaigns.view_group"

    def get_queryset(self) -> QuerySet[models.Group]:
        """Return queryset with related objects."""
        return models.Group.objects.prefetch_related("partners")


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Group model."""

    model = models.Group
    form_class = forms.GroupForm
    template_name = "campaigns/group/form.html"
    permission_required = "campaigns.add_group"
    success_url = reverse_lazy("apps.campaigns:group-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Group")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set user tracking fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Group model."""

    model = models.Group
    form_class = forms.GroupForm
    template_name = "campaigns/group/form.html"
    permission_required = "campaigns.change_group"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.campaigns:group-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Group')}: {self.object.name}"
        context["action"] = "update"
        return context

    def form_valid(self, form):
        """Update user tracking fields."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Group model."""

    model = models.Group
    template_name = "campaigns/group/confirm_delete.html"
    permission_required = "campaigns.delete_group"
    success_url = reverse_lazy("apps.campaigns:group-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Group')}: {self.object.name}"
        return context


class GroupBulkAddPartnersView(
    LoginRequiredMixin, PermissionRequiredMixin, View
):
    """View for bulk adding partners to a group via file upload."""

    permission_required = "campaigns.change_group"
    template_name = "campaigns/group/bulk_add_partners.html"

    def get(self, request, pk):
        """Display the bulk add partners form."""
        from django.shortcuts import get_object_or_404, render

        group = get_object_or_404(models.Group, pk=pk)
        form = forms.BulkAddPartnersForm(group=group)

        context = {
            "group": group,
            "form": form,
            "title": f"{_('Bulk Add Partners')}: {group.name}",
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Process the uploaded file and add partners to the group."""
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, render

        group = get_object_or_404(models.Group, pk=pk)
        form = forms.BulkAddPartnersForm(
            request.POST, request.FILES, group=group
        )

        if form.is_valid():
            try:
                results = form.process_file()

                # Add success message with results
                added_count = len(results["added"])
                not_found_count = len(results["not_found"])
                already_in_group_count = len(results["already_in_group"])

                if added_count > 0:
                    messages.success(
                        request,
                        _(
                            f"Successfully added {added_count} partner(s) to the group."
                        ),
                    )

                if already_in_group_count > 0:
                    messages.info(
                        request,
                        _(
                            f"{already_in_group_count} partner(s) were already in the group."
                        ),
                    )

                if not_found_count > 0:
                    messages.warning(
                        request,
                        _(
                            f"{not_found_count} document(s) were not found in the system."
                        ),
                    )

                context = {
                    "group": group,
                    "form": form,
                    "results": results,
                    "title": f"{_('Bulk Add Partners')}: {group.name}",
                }
                return render(request, self.template_name, context)

            except Exception as e:
                logger.error(
                    f"Error processing bulk add partners for group {pk}: {e}"
                )
                messages.error(
                    request,
                    _("An error occurred while processing the file."),
                )

        context = {
            "group": group,
            "form": form,
            "title": f"{_('Bulk Add Partners')}: {group.name}",
        }
        return render(request, self.template_name, context)


# AJAX Views
class GroupDebtAjaxView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX view to get group debt information."""

    permission_required = "campaigns.view_group"

    def get(self, request, group_id):
        """Return group debt information as JSON."""
        from django.http import JsonResponse
        from django.shortcuts import get_object_or_404

        try:
            group = get_object_or_404(models.Group, id=group_id)

            # Get debt summary
            debt_summary = group.get_debt_summary()
            total_debt = group.total_outstanding_debt

            return JsonResponse(
                {
                    "success": True,
                    "total_debt": float(total_debt),
                    "debt_summary": {
                        "total_debt": float(debt_summary["total_debt"]),
                        "credit_debt": float(debt_summary["credit_debt"]),
                        "contribution_debt": float(
                            debt_summary["contribution_debt"]
                        ),
                        "social_security_debt": float(
                            debt_summary["social_security_debt"]
                        ),
                        "penalty_debt": float(debt_summary["penalty_debt"]),
                        "partners_with_debt": debt_summary[
                            "partners_with_debt"
                        ],
                        "overdue_installments": debt_summary[
                            "overdue_installments"
                        ],
                        "overdue_contributions": debt_summary[
                            "overdue_contributions"
                        ],
                        "overdue_social_security": debt_summary[
                            "overdue_social_security"
                        ],
                        "overdue_penalties": debt_summary["overdue_penalties"],
                    },
                    "group_name": group.name,
                    "partner_count": group.partner_count,
                }
            )
        except Exception as e:
            logger.error(f"Error getting group debt for group {group_id}: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": "Error retrieving group debt information",
                },
                status=500,
            )
