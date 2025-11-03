import logging
from typing import Any, Dict

from constance import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.partners import mixins as partner_mixins
from apps.partners import models as partner_models
from apps.payments import choices, filtersets, forms, mixins, models

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


# ============================================================================
# Payment Receipt Views
# ============================================================================


class PaymentReceiptListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View to list payment receipts with filtering capabilities."""

    model = models.PaymentReceipt
    template_name = "payments/receipt/list.html"
    context_object_name = "receipts"
    filterset_class = filtersets.PaymentReceiptFilter
    permission_required = "payments.view_paymentreceipt"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.PaymentReceipt]:
        """Get optimized queryset for receipt list."""
        return models.PaymentReceipt.objects.select_related(
            "partner", "validated_by"
        ).order_by("-created")


class PaymentReceiptDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display payment receipt details."""

    model = models.PaymentReceipt
    template_name = "payments/receipt/detail.html"
    context_object_name = "receipt"
    permission_required = "payments.view_paymentreceipt"

    def get_queryset(self) -> QuerySet[models.PaymentReceipt]:
        """Get optimized queryset for receipt detail."""
        return models.PaymentReceipt.objects.select_related(
            "partner", "validated_by"
        )


class PaymentReceiptCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """View to create a new payment receipt."""

    model = models.PaymentReceipt
    form_class = forms.PaymentReceiptForm
    template_name = "payments/receipt/form.html"
    permission_required = "payments.add_paymentreceipt"

    def get_success_url(self) -> str:
        """Return success URL after receipt creation."""
        return reverse(
            "apps.payments:payment-receipt-detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        """Handle valid form submission."""
        # Set user tracking fields
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            _("Payment receipt has been created successfully."),
        )

        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)
        context["form_title"] = _("New Payment Receipt")
        context["submit_text"] = _("Save Receipt")
        return context


class PaymentReceiptUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """View to update a payment receipt."""

    model = models.PaymentReceipt
    form_class = forms.PaymentReceiptForm
    template_name = "payments/receipt/form.html"
    permission_required = "payments.change_paymentreceipt"

    def get_success_url(self) -> str:
        """Return success URL after receipt update."""
        return reverse(
            "apps.payments:payment-receipt-detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        """Handle valid form submission."""
        # Set modified_by
        form.instance.modified_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            _("Payment receipt has been updated successfully."),
        )

        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)
        context["form_title"] = _("Edit Payment Receipt")
        context["submit_text"] = _("Update Receipt")
        return context


class PaymentReceiptDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """View to delete a payment receipt."""

    model = models.PaymentReceipt
    context_object_name = "receipt"
    template_name = "payments/receipt/confirm_delete.html"
    permission_required = "payments.delete_paymentreceipt"
    success_url = reverse_lazy("apps.payments:payment-receipt-list")

    def delete(self, request, *args, **kwargs):
        """Handle receipt deletion."""
        receipt = self.get_object()

        response = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            _("Payment receipt has been deleted successfully."),
        )
        return response


# ============================================================================
# Magic Payment Link Views
# ============================================================================


class MagicPaymentLinkCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """View for creating Magic Payment Links."""

    template_name = "payments/magic_link/create.html"
    form_class = forms.MagicPaymentLinkForm
    permission_required = "payments.add_magicpaymentlink"
    success_url = reverse_lazy("apps.payments:magic-link-list")

    def get_form_kwargs(self):
        """Get form kwargs, removing 'instance' for non-ModelForm."""
        kwargs = super().get_form_kwargs()
        # Remove 'instance' key since MagicPaymentLinkForm is a Form, not ModelForm
        kwargs.pop("instance", None)
        return kwargs

    def form_valid(self, form):
        """Process form and create magic link."""
        from apps.partners.services import PartnerDebtService
        from apps.payments.utils import payment_links

        document_number = form.cleaned_data["document_number"]
        name = form.cleaned_data.get("name")
        hours_to_expire = form.cleaned_data.get("hours_to_expire", 24)
        include_upcoming = form.cleaned_data.get("include_upcoming", False)

        try:
            # Get partner
            partner = partner_models.Partner.objects.get(
                document_number=document_number
            )

            # Get debts
            debts = PartnerDebtService.get_partner_debt_objects_for_payment(
                partner, include_upcoming=include_upcoming
            )

            if not debts:
                messages.warning(
                    self.request,
                    _(
                        "El socio con DNI %(document)s no tiene deudas pendientes."
                    )
                    % {"document": document_number},
                )
                return self.form_invalid(form)

            # Create magic link
            with transaction.atomic():
                magic_link = payment_links.create_magic_payment_link(
                    partner=partner,
                    debts=debts,
                    title=name,
                    hours_to_expire=hours_to_expire,
                    user=self.request.user,
                )

            messages.success(
                self.request,
                _(
                    "Magic Link creado exitosamente para %(partner)s. "
                    "Total: PEN %(amount)s - %(count)d deuda(s)"
                )
                % {
                    "partner": partner.full_name,
                    "amount": f"{magic_link.amount:,.2f}",
                    "count": magic_link.debt_count,
                },
            )

            return redirect("apps.payments:magic-link-detail", pk=magic_link.pk)

        except partner_models.Partner.DoesNotExist:
            messages.error(
                self.request,
                _("No se encontró un socio con el DNI %(document)s")
                % {"document": document_number},
            )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                _("Error al crear el Magic Link: %(error)s")
                % {"error": str(e)},
            )
            return self.form_invalid(form)


class MagicPaymentLinkListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View for listing Magic Payment Links."""

    model = models.MagicPaymentLink
    template_name = "payments/magic_link/list.html"
    context_object_name = "magic_links"
    permission_required = "payments.view_magicpaymentlink"
    filterset_class = filtersets.MagicPaymentLinkFilter
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self):
        """Get optimized queryset."""
        return (
            models.MagicPaymentLink.objects.filter(
                source=choices.MagicLinkSource.MANUAL
            )
            .select_related("partner", "payment", "created_by")
            .order_by("-created")
        )


class MagicPaymentLinkDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View for Magic Payment Link details (admin)."""

    model = models.MagicPaymentLink
    template_name = "payments/magic_link/detail.html"
    context_object_name = "magic_link"
    permission_required = "payments.view_magicpaymentlink"

    def get_queryset(self):
        """Optimize queryset."""
        return models.MagicPaymentLink.objects.select_related(
            "partner", "payment", "created_by", "modified_by"
        )

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        magic_link = self.object

        context["title"] = magic_link.name

        # Check and update expiration status
        magic_link.check_and_update_expiration()

        # Build full URL
        context["full_url"] = magic_link.get_full_url(self.request)

        # Get debt details from metadata
        debts_metadata = magic_link.metadata.get("debts", [])
        context["debts_count"] = len(debts_metadata)
        context["debts"] = debts_metadata

        return context


class MagicPaymentLinkPublicView(TemplateView):
    """Public view for partners to see and pay their Magic Link."""

    template_name = "payments/magic_link/public.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request."""
        token = kwargs.get("token")

        try:
            magic_link = models.MagicPaymentLink.objects.select_related(
                "partner", "payment"
            ).get(token=token)
        except models.MagicPaymentLink.DoesNotExist:
            raise Http404(_("Link de pago no encontrado"))

        # Check and update expiration
        magic_link.check_and_update_expiration()

        # Check if link is still valid
        if not magic_link.is_active:
            return render(
                request,
                "payments/magic_link/expired.html",
                {
                    "magic_link": magic_link,
                    "title": _("Link Expirado"),
                },
            )

        # Get debt objects from metadata
        debts_data = self._get_debts_from_metadata(magic_link)

        context = {
            "magic_link": magic_link,
            "partner": magic_link.partner,
            "debts": debts_data,
            "title": magic_link.name,
            "culqi_public_key": settings.CULQI_PUBLIC_KEY,
            "culqi_rsa_id": settings.CULQI_RSA_ID,
            "culqi_rsa_public_key": settings.CULQI_RSA_PUBLIC_KEY,
        }

        return render(request, self.template_name, context)

    def _get_debts_from_metadata(self, magic_link):
        """Extract and enrich debt information from metadata."""
        from apps.compliance.models import Contribution, Penalty, SocialSecurity
        from apps.credits.models import Installment

        debts_metadata = magic_link.metadata.get("debts", [])
        debts_data = []

        for debt_meta in debts_metadata:
            debt_type = debt_meta.get("type")
            debt_id = debt_meta.get("id")

            try:
                if debt_type == "installment":
                    debt_obj = Installment.objects.select_related("credit").get(
                        id=debt_id
                    )
                    debt_info = {
                        "type": "Aporte",
                        "description": f"Aporte #{debt_meta.get('number')}",
                        "amount": debt_meta.get("amount"),
                        "due_date": debt_meta.get("due_date"),
                        "object": debt_obj,
                    }
                elif debt_type == "contribution":
                    debt_obj = Contribution.objects.get(id=debt_id)
                    debt_info = {
                        "type": "Aportación",
                        "description": debt_obj.name,
                        "amount": debt_meta.get("amount"),
                        "due_date": debt_meta.get("due_date"),
                        "object": debt_obj,
                    }
                elif debt_type == "socialsecurity":
                    debt_obj = SocialSecurity.objects.get(id=debt_id)
                    debt_info = {
                        "type": "Seguridad Social",
                        "description": debt_obj.name,
                        "amount": debt_meta.get("amount"),
                        "due_date": debt_meta.get("due_date"),
                        "object": debt_obj,
                    }
                elif debt_type == "penalty":
                    debt_obj = Penalty.objects.get(id=debt_id)
                    debt_info = {
                        "type": "Penalidad",
                        "description": debt_obj.name,
                        "amount": debt_meta.get("amount"),
                        "due_date": debt_meta.get("due_date"),
                        "object": debt_obj,
                    }
                else:
                    continue

                debts_data.append(debt_info)

            except Exception:
                # If debt object not found, use metadata only
                debt_info = {
                    "type": debt_type.capitalize(),
                    "description": debt_meta.get(
                        "name", f"{debt_type} #{debt_id}"
                    ),
                    "amount": debt_meta.get("amount"),
                    "due_date": debt_meta.get("due_date"),
                    "object": None,
                }
                debts_data.append(debt_info)

        return debts_data
