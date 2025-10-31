import logging
from typing import Any, Dict

from constance import config
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
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

from apps.support import filtersets, forms, models

logger = logging.getLogger(__name__)


class TicketListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for Ticket model with filtering."""

    model = models.Ticket
    filterset_class = filtersets.TicketFilterSet
    template_name = "support/ticket/list.html"
    context_object_name = "tickets"
    permission_required = "support.view_ticket"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Ticket]:
        """Return filtered and ordered queryset."""
        return models.Ticket.objects.select_related(
            "partner", "assigned_to", "assigned_to__position"
        ).order_by("-created")


class TicketDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Ticket model."""

    model = models.Ticket
    template_name = "support/ticket/detail.html"
    context_object_name = "ticket"
    permission_required = "support.view_ticket"

    def get_queryset(self) -> QuerySet[models.Ticket]:
        """Return queryset with related objects."""
        return models.Ticket.objects.select_related(
            "partner",
            "assigned_to",
            "assigned_to__position",
            "created_by",
            "modified_by",
        ).prefetch_related(
            "comments__created_by"
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["comment_form"] = forms.TicketCommentForm()
        context["status_form"] = forms.TicketStatusUpdateForm(instance=self.object)
        return context


class TicketCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Ticket model."""

    model = models.Ticket
    form_class = forms.TicketForm
    template_name = "support/ticket/form.html"
    permission_required = "support.add_ticket"
    success_url = reverse_lazy("apps.support:ticket-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Ticket")
        context["action"] = "create"
        return context

    def form_valid(self, form):
        """Set created_by before saving."""
        form.instance.created_by = self.request.user
        messages.success(self.request, _("Ticket created successfully."))
        return super().form_valid(form)


class TicketUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Ticket model."""

    model = models.Ticket
    form_class = forms.TicketForm
    template_name = "support/ticket/form.html"
    permission_required = "support.change_ticket"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy("apps.support:ticket-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Edit Ticket')}: #{self.object.pk}"
        context["action"] = "update"
        return context

    def form_valid(self, form):
        """Update modified_by before saving."""
        form.instance.modified_by = self.request.user
        messages.success(self.request, _("Ticket updated successfully."))
        return super().form_valid(form)


class TicketDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Ticket model."""

    model = models.Ticket
    template_name = "support/ticket/confirm_delete.html"
    permission_required = "support.delete_ticket"
    success_url = reverse_lazy("apps.support:ticket-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"{_('Delete Ticket')}: #{self.object.pk}"
        return context

    def form_valid(self, form):
        """Add success message."""
        messages.success(self.request, _("Ticket deleted successfully."))
        return super().form_valid(form)


class TicketCommentCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View to add comments to a ticket."""

    permission_required = "support.add_ticketcomment"

    def post(self, request, pk):
        """Handle comment form submission."""
        ticket = get_object_or_404(models.Ticket, pk=pk)
        form = forms.TicketCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.created_by = request.user
            comment.save()
            messages.success(request, _("Comment added successfully."))
        else:
            messages.error(request, _("Error adding comment. Please try again."))

        return redirect("apps.support:ticket-detail", pk=pk)


class TicketStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View to update ticket status."""

    permission_required = "support.change_ticket"

    def post(self, request, pk):
        """Handle status update form submission."""
        ticket = get_object_or_404(models.Ticket, pk=pk)
        form = forms.TicketStatusUpdateForm(request.POST, instance=ticket)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.modified_by = request.user
            ticket.save()
            messages.success(request, _("Ticket status updated successfully."))
        else:
            messages.error(request, _("Error updating status. Please try again."))

        return redirect("apps.support:ticket-detail", pk=pk)
