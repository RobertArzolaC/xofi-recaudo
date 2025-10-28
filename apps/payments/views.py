import logging
from typing import Any, Dict

from constance import config
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db import transaction
from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.partners import mixins as partner_mixins
from apps.payments import filtersets, forms, mixins, models

logger = logging.getLogger(__name__)


class PaymentListView(
    partner_mixins.PartnerAccessMixin, PermissionRequiredMixin, FilterView
):
    """View to list payments with filtering capabilities."""

    model = models.Payment
    template_name = "payments/list.html"
    context_object_name = "payments"
    filterset_class = filtersets.PaymentFilter
    permission_required = "payments.view_payment"
    paginate_by = config.ITEMS_PER_PAGE


class PaymentDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display payment details."""

    model = models.Payment
    template_name = "payments/detail.html"
    context_object_name = "payment"
    permission_required = "payments.view_payment"

    def get_queryset(self) -> QuerySet[models.Payment]:
        """Get optimized queryset for payment detail."""
        return models.Payment.objects.select_related(
            "partner"
        ).prefetch_related("concept_allocations__concept_object")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)
        payment = self.get_object()

        # Get payment summary
        context["payment_summary"] = {
            "total_allocated": payment.total_allocated,
            "unallocated_amount": payment.unallocated_amount,
            "is_fully_allocated": payment.is_fully_allocated,
        }

        return context


class PaymentCreateView(
    mixins.PaymentAllocationMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """View to create a new payment."""

    model = models.Payment
    form_class = forms.PaymentForm
    template_name = "payments/form.html"
    permission_required = "payments.add_payment"

    def get_success_url(self) -> str:
        """Return success URL after payment creation."""
        return reverse(
            "apps.payments:payment-detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        """Handle valid form submission with allocation processing."""
        # Set user tracking fields
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user

        # Process payment creation and allocations in a transaction
        with transaction.atomic():
            response = super().form_valid(form)

            # Process allocations if any were submitted
            allocations_data = self._extract_allocations_from_request()
            if allocations_data:
                created_allocations = self._create_payment_allocations(
                    allocations_data
                )

                # Add allocation summary to success message
                allocation_count = len(created_allocations)
                total_allocated = sum(
                    alloc.amount_applied for alloc in created_allocations
                )

                messages.success(
                    self.request,
                    _(
                        "Payment #{} has been created successfully with {} allocation(s) totaling ${}."
                    ).format(
                        self.object.payment_number,
                        allocation_count,
                        total_allocated,
                    ),
                )
            else:
                messages.success(
                    self.request,
                    _("Payment #{} has been created successfully.").format(
                        self.object.payment_number
                    ),
                )

        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)
        context["form_title"] = _("Create Payment")
        context["submit_text"] = _("Create Payment")
        return context


class PaymentUpdateView(
    mixins.PaymentAllocationMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """View to update an existing payment."""

    model = models.Payment
    form_class = forms.PaymentForm
    template_name = "payments/form.html"
    permission_required = "payments.change_payment"

    def get_success_url(self) -> str:
        """Return success URL after payment update."""
        return reverse(
            "apps.payments:payment-detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        """Handle valid form submission with allocation processing."""
        # Update modified_by field
        form.instance.modified_by = self.request.user

        # Process payment update and allocations in a transaction
        with transaction.atomic():
            response = super().form_valid(form)

            # Process allocations if any were submitted
            allocations_data = self._extract_allocations_from_request()
            if allocations_data:
                # Clear existing allocations and create new ones
                self.object.concept_allocations.all().delete()
                created_allocations = self._create_payment_allocations(
                    allocations_data
                )

                # Add allocation summary to success message
                allocation_count = len(created_allocations)
                total_allocated = sum(
                    alloc.amount_applied for alloc in created_allocations
                )

                messages.success(
                    self.request,
                    _(
                        "Payment #{} has been updated successfully with {} allocation(s) totaling ${}."
                    ).format(
                        self.object.payment_number,
                        allocation_count,
                        total_allocated,
                    ),
                )
            else:
                # Clear allocations if none were submitted
                self.object.concept_allocations.all().delete()
                messages.success(
                    self.request,
                    _("Payment #{} has been updated successfully.").format(
                        self.object.payment_number
                    ),
                )

        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)
        context["form_title"] = _("Edit Payment")
        context["submit_text"] = _("Update Payment")
        return context


class PaymentDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """View to delete a payment."""

    model = models.Payment
    template_name = "payments/confirm_delete.html"
    permission_required = "payments.delete_payment"
    success_url = reverse_lazy("apps.payments:payment-list")

    def delete(self, request, *args, **kwargs):
        """Handle payment deletion."""
        payment = self.get_object()
        payment_number = payment.payment_number

        response = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            _("Payment #{} has been deleted successfully.").format(
                payment_number
            ),
        )
        return response
