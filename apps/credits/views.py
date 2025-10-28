from constance import config
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from apps.credits import choices, filtersets, forms, models
from apps.partners import mixins as partner_mixins


class ProductTypeListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """View to list all product types with filtering."""

    model = models.ProductType
    template_name = "credits/product_type/list.html"
    context_object_name = "product_types"
    permission_required = "credits.view_producttype"
    filterset_class = filtersets.ProductTypeFilter
    paginate_by = config.ITEMS_PER_PAGE


class ProductTypeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View to display product type details."""

    model = models.ProductType
    template_name = "credits/product_type/detail.html"
    context_object_name = "product_type"
    permission_required = "credits.view_producttype"


class ProductTypeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new product type."""

    model = models.ProductType
    template_name = "credits/product_type/form.html"
    form_class = forms.ProductTypeForm
    permission_required = "credits.add_producttype"
    success_message = _("Product type created successfully.")
    success_url = reverse_lazy("apps.credits:product_type_list")

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ProductTypeUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing product type."""

    model = models.ProductType
    template_name = "credits/product_type/form.html"
    form_class = forms.ProductTypeForm
    permission_required = "credits.change_producttype"
    success_message = _("Product type updated successfully.")
    success_url = reverse_lazy("apps.credits:product_type_list")

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ProductTypeDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a product type."""

    model = models.ProductType
    template_name = "credits/product_type/delete.html"
    context_object_name = "product_type"
    permission_required = "credits.delete_producttype"
    success_message = _("Product type deleted successfully.")
    success_url = reverse_lazy("apps.credits:product_type_list")


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """View to list all products with filtering."""

    model = models.Product
    template_name = "credits/product/list.html"
    context_object_name = "products"
    permission_required = "credits.view_product"
    filterset_class = filtersets.ProductFilter
    paginate_by = config.ITEMS_PER_PAGE


class ProductDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View to display product details."""

    model = models.Product
    template_name = "credits/product/detail.html"
    context_object_name = "product"
    permission_required = "credits.view_product"


class ProductCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new product."""

    model = models.Product
    template_name = "credits/product/form.html"
    form_class = forms.ProductForm
    permission_required = "credits.add_product"
    success_message = _("Product created successfully.")
    success_url = reverse_lazy("apps.credits:product_list")

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing product."""

    model = models.Product
    template_name = "credits/product/form.html"
    form_class = forms.ProductForm
    permission_required = "credits.change_product"
    success_message = _("Product updated successfully.")
    success_url = reverse_lazy("apps.credits:product_list")

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class ProductDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a product."""

    model = models.Product
    template_name = "credits/product/delete.html"
    context_object_name = "product"
    permission_required = "credits.delete_product"
    success_message = _("Product deleted successfully.")
    success_url = reverse_lazy("apps.credits:product_list")


class CreditListView(
    partner_mixins.PartnerAccessMixin, PermissionRequiredMixin, FilterView
):
    """View to list all credits with filtering."""

    model = models.Credit
    template_name = "credits/credit/list.html"
    context_object_name = "credits"
    permission_required = "credits.view_credit"
    filterset_class = filtersets.CreditFilter
    paginate_by = config.ITEMS_PER_PAGE


class CreditDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View to display credit details."""

    model = models.Credit
    template_name = "credits/credit/detail.html"
    context_object_name = "credit"
    permission_required = "credits.view_credit"

    def get_context_data(self, **kwargs):
        """Add additional context data for the credit detail view."""
        context = super().get_context_data(**kwargs)
        credit = self.object

        # Add related installments
        context["installments"] = credit.get_current_installments()

        # Add status history
        context["status_history"] = credit.status_history.select_related("modified_by")[
            :10
        ]

        # Check if user can change status
        context["can_change_status"] = self.request.user.has_perm(
            "credits.change_credit_status"
        )

        return context


class CreditCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new credit."""

    model = models.Credit
    template_name = "credits/credit/form.html"
    form_class = forms.CreditForm
    permission_required = "credits.add_credit"
    success_message = _("Credit created successfully.")
    success_url = reverse_lazy("apps.credits:credit_list")

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing credit."""

    model = models.Credit
    template_name = "credits/credit/form.html"
    form_class = forms.CreditForm
    permission_required = "credits.change_credit"
    success_message = _("Credit updated successfully.")
    success_url = reverse_lazy("apps.credits:credit_list")

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a credit."""

    model = models.Credit
    template_name = "credits/credit/delete.html"
    context_object_name = "credit"
    permission_required = "credits.delete_credit"
    success_message = _("Credit deleted successfully.")
    success_url = reverse_lazy("apps.credits:credit_list")


class CreditApplicationListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View to list all credit applications with filtering."""

    model = models.CreditApplication
    template_name = "credits/credit_application/list.html"
    context_object_name = "credit_applications"
    permission_required = "credits.view_creditapplication"
    filterset_class = filtersets.CreditApplicationFilter
    paginate_by = config.ITEMS_PER_PAGE


class CreditApplicationDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display credit application details."""

    model = models.CreditApplication
    template_name = "credits/credit_application/detail.html"
    context_object_name = "credit_application"
    permission_required = "credits.view_creditapplication"


class CreditApplicationCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new credit application."""

    model = models.CreditApplication
    template_name = "credits/credit_application/form.html"
    form_class = forms.CreditApplicationForm
    permission_required = "credits.add_creditapplication"
    success_message = _("Credit application created successfully.")
    success_url = reverse_lazy("apps.credits:credit_application_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["is_create"] = True
        return kwargs

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditApplicationUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing credit application."""

    model = models.CreditApplication
    template_name = "credits/credit_application/form.html"
    form_class = forms.CreditApplicationForm
    permission_required = "credits.change_creditapplication"
    success_message = _("Credit application updated successfully.")
    success_url = reverse_lazy("apps.credits:credit_application_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["is_create"] = False
        return kwargs

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditApplicationDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a credit application."""

    model = models.CreditApplication
    template_name = "credits/credit_application/delete.html"
    context_object_name = "credit_application"
    permission_required = "credits.delete_creditapplication"
    success_message = _("Credit application deleted successfully.")
    success_url = reverse_lazy("apps.credits:credit_application_list")


class CreditRescheduleRequestListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View to list all credit reschedule requests with filtering."""

    model = models.CreditRescheduleRequest
    template_name = "credits/credit_reschedule_request/list.html"
    context_object_name = "credit_reschedule_requests"
    permission_required = "credits.view_creditreschedulerequest"
    filterset_class = filtersets.CreditRescheduleRequestFilter
    paginate_by = config.ITEMS_PER_PAGE


class CreditRescheduleRequestDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display credit reschedule request details."""

    model = models.CreditRescheduleRequest
    template_name = "credits/credit_reschedule_request/detail.html"
    context_object_name = "credit_reschedule_request"
    permission_required = "credits.view_creditreschedulerequest"


class CreditRescheduleRequestCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new credit reschedule request."""

    model = models.CreditRescheduleRequest
    template_name = "credits/credit_reschedule_request/form.html"
    form_class = forms.CreditRescheduleRequestForm
    permission_required = "credits.add_creditreschedulerequest"
    success_message = _("Credit reschedule request created successfully.")
    success_url = reverse_lazy("apps.credits:credit_reschedule_request_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_create"] = True
        return kwargs

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditRescheduleRequestUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing credit reschedule request."""

    model = models.CreditRescheduleRequest
    template_name = "credits/credit_reschedule_request/form.html"
    form_class = forms.CreditRescheduleRequestForm
    permission_required = "credits.change_creditreschedulerequest"
    success_message = _("Credit reschedule request updated successfully.")
    success_url = reverse_lazy("apps.credits:credit_reschedule_request_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_create"] = False
        return kwargs

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditRescheduleRequestDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a credit reschedule request."""

    model = models.CreditRescheduleRequest
    template_name = "credits/credit_reschedule_request/confirm_delete.html"
    context_object_name = "credit_reschedule_request"
    permission_required = "credits.delete_creditreschedulerequest"
    success_message = _("Credit reschedule request deleted successfully.")
    success_url = reverse_lazy("apps.credits:credit_reschedule_request_list")


class CreditApplicationChangeStatusView(
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    """View to change the status of a credit application."""

    template_name = "credits/credit_application/change_status.html"
    form_class = forms.CreditApplicationStatusChangeForm
    permission_required = "credits.change_creditapplication"

    def dispatch(self, request, *args, **kwargs):
        """Get the credit application instance."""
        self.application = get_object_or_404(models.CreditApplication, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["application"] = self.application
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add application to context."""
        context = super().get_context_data(**kwargs)
        context["application"] = self.application
        context["current_status_duration"] = (
            self.application.get_current_status_duration()
        )
        context["status_history"] = self.application.status_history.select_related(
            "modified_by"
        )[:10]
        return context

    def form_valid(self, form):
        """Process status change."""
        new_status = form.cleaned_data["status"]
        note = form.cleaned_data["note"]

        # Change status using the model method
        success = self.application.change_status(
            new_status=new_status, user=self.request.user, note=note
        )

        if success:
            status_display = dict(choices.CreditApplicationStatus.choices)[new_status]
            messages.success(
                self.request,
                _("Application status changed to '{status}' successfully.").format(
                    status=status_display
                ),
            )
        else:
            messages.error(
                self.request,
                _(
                    "Could not change status. Please check the current status and try again."
                ),
            )

        return redirect(
            "apps.credits:credit_application_detail", pk=self.application.pk
        )

    def get_success_url(self):
        """Redirect back to application detail."""
        return reverse_lazy(
            "apps.credits:credit_application_detail",
            kwargs={"pk": self.application.pk},
        )


class CreditApplicationPaymentSchedulePDFView(
    LoginRequiredMixin, PermissionRequiredMixin, View
):
    """View to generate payment schedule PDF for credit application."""

    permission_required = "credits.view_creditapplication"

    def get(self, request, pk):
        """Generate and return payment schedule PDF."""
        application = get_object_or_404(models.CreditApplication, pk=pk)

        # Check if application has payment schedule
        if not application.payment_schedule:
            messages.error(
                request,
                _("Payment schedule is not available for this application."),
            )
            return redirect("apps.credits:credit_application_detail", pk=application.pk)

        context = {
            "application": application,
            "payment_schedule": application.payment_schedule,
        }

        # Render the HTML template
        html_content = render_to_string(
            "credits/credit_application/payment_schedule_pdf.html", context
        )

        # Create HTTP response with PDF content type
        response = HttpResponse(content_type="text/html")
        response["Content-Disposition"] = (
            f'inline; filename="payment_schedule_{application.id}.html"'
        )

        response.write(html_content)
        return response


class CreditChangeStatusView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """View to change the status of a credit."""

    template_name = "credits/credit/change_status.html"
    form_class = forms.CreditStatusChangeForm
    permission_required = "credits.change_credit_status"

    def dispatch(self, request, *args, **kwargs):
        """Get the credit instance."""
        self.credit = get_object_or_404(models.Credit, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["credit"] = self.credit
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add credit to context."""
        context = super().get_context_data(**kwargs)
        context["credit"] = self.credit
        context["current_status_duration"] = self.credit.get_current_status_duration()
        context["status_history"] = self.credit.status_history.select_related(
            "modified_by"
        )[:10]
        return context

    def form_valid(self, form):
        """Process status change."""
        new_status = form.cleaned_data["status"]
        note = form.cleaned_data["note"]

        # Change status using the model method
        success = self.credit.change_status(
            new_status=new_status, user=self.request.user, note=note
        )

        if success:
            status_display = dict(choices.CreditStatus.choices)[new_status]
            messages.success(
                self.request,
                _("Credit status changed to '{status}' successfully.").format(
                    status=status_display
                ),
            )
        else:
            messages.error(
                self.request,
                _(
                    "Could not change status. Please check the current status and try again."
                ),
            )

        return redirect("apps.credits:credit_detail", pk=self.credit.pk)

    def get_success_url(self):
        """Redirect back to credit detail."""
        return reverse_lazy(
            "apps.credits:credit_detail",
            kwargs={"pk": self.credit.pk},
        )


class CreditRefinanceRequestListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View to list all credit refinance requests with filtering."""

    model = models.CreditRefinanceRequest
    template_name = "credits/credit_refinance_request/list.html"
    context_object_name = "credit_refinance_requests"
    permission_required = "credits.view_creditrefinancerequest"
    paginate_by = 20
    filterset_class = filtersets.CreditRefinanceRequestFilter


class CreditRefinanceRequestDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display credit refinance request details."""

    model = models.CreditRefinanceRequest
    template_name = "credits/credit_refinance_request/detail.html"
    context_object_name = "credit_refinance_request"
    permission_required = "credits.view_creditrefinancerequest"


class CreditRefinanceRequestCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new credit refinance request."""

    model = models.CreditRefinanceRequest
    template_name = "credits/credit_refinance_request/form.html"
    form_class = forms.CreditRefinanceRequestForm
    permission_required = "credits.add_creditrefinancerequest"
    success_message = _("Credit refinance request created successfully.")
    success_url = reverse_lazy("apps.credits:credit_refinance_request_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_create"] = True
        return kwargs

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditRefinanceRequestUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing credit refinance request."""

    model = models.CreditRefinanceRequest
    template_name = "credits/credit_refinance_request/form.html"
    form_class = forms.CreditRefinanceRequestForm
    permission_required = "credits.change_creditrefinancerequest"
    success_message = _("Credit refinance request updated successfully.")
    success_url = reverse_lazy("apps.credits:credit_refinance_request_list")

    def get_form_kwargs(self):
        """Pass additional kwargs to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_create"] = False
        return kwargs

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditRefinanceRequestDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a credit refinance request."""

    model = models.CreditRefinanceRequest
    template_name = "credits/credit_refinance_request/confirm_delete.html"
    context_object_name = "credit_refinance_request"
    permission_required = "credits.delete_creditrefinancerequest"
    success_message = _("Credit refinance request deleted successfully.")
    success_url = reverse_lazy("apps.credits:credit_refinance_request_list")


# ============================================================================
# CreditDisbursement Views
# ============================================================================


class CreditDisbursementListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView
):
    """View to list all credit disbursements with filtering."""

    model = models.CreditDisbursement
    template_name = "credits/disbursement/list.html"
    context_object_name = "disbursements"
    permission_required = "credits.view_creditdisbursement"
    filterset_class = filtersets.CreditDisbursementFilter
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self):
        """Get queryset with related data."""
        return (
            super()
            .get_queryset()
            .select_related(
                "credit",
                "credit__partner",
                "credit__product",
                "created_by",
                "modified_by",
            )
            .order_by("-scheduled_date", "-created")
        )


class CreditDisbursementDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    """View to display credit disbursement details."""

    model = models.CreditDisbursement
    template_name = "credits/disbursement/detail.html"
    context_object_name = "disbursement"
    permission_required = "credits.view_creditdisbursement"

    def get_queryset(self):
        """Get queryset with related data."""
        return (
            super()
            .get_queryset()
            .select_related(
                "credit",
                "credit__partner",
                "credit__product",
                "created_by",
                "modified_by",
            )
            .prefetch_related("status_history")
        )

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["status_history"] = self.object.status_history.order_by("-created")
        return context


class CreditDisbursementCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View to create a new credit disbursement."""

    model = models.CreditDisbursement
    template_name = "credits/disbursement/form.html"
    form_class = forms.CreditDisbursementForm
    permission_required = "credits.add_creditdisbursement"
    success_message = _("Credit disbursement created successfully.")

    def get_success_url(self):
        """Return to disbursement detail page."""
        return reverse_lazy(
            "apps.credits:disbursement_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Credit Disbursement")
        return context

    def form_valid(self, form):
        """Set the created_by and modified_by fields."""
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditDisbursementUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View to update an existing credit disbursement."""

    model = models.CreditDisbursement
    template_name = "credits/disbursement/form.html"
    form_class = forms.CreditDisbursementForm
    permission_required = "credits.change_creditdisbursement"
    success_message = _("Credit disbursement updated successfully.")

    def get_success_url(self):
        """Return to disbursement detail page."""
        return reverse_lazy(
            "apps.credits:disbursement_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update Credit Disbursement")
        return context

    def form_valid(self, form):
        """Set the modified_by field."""
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class CreditDisbursementDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    """View to delete a credit disbursement."""

    model = models.CreditDisbursement
    template_name = "credits/disbursement/delete.html"
    context_object_name = "disbursement"
    permission_required = "credits.delete_creditdisbursement"
    success_message = _("Credit disbursement deleted successfully.")
    success_url = reverse_lazy("apps.credits:disbursement_list")


class CreditDisbursementChangeStatusView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, FormView
):
    """View to change the status of a credit disbursement."""

    template_name = "credits/disbursement/change_status.html"
    form_class = forms.CreditDisbursementStatusChangeForm
    permission_required = "credits.change_creditdisbursement"
    success_message = _("Disbursement status changed successfully.")

    def get_disbursement(self):
        """Get the disbursement object."""
        if not hasattr(self, "_disbursement"):
            self._disbursement = get_object_or_404(
                models.CreditDisbursement.objects.select_related(
                    "credit",
                    "credit__partner",
                    "credit__product",
                ),
                pk=self.kwargs["pk"],
            )
        return self._disbursement

    def get_form_kwargs(self):
        """Add disbursement and user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["disbursement"] = self.get_disbursement()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add disbursement to context."""
        context = super().get_context_data(**kwargs)
        context["disbursement"] = self.get_disbursement()
        context["status_history"] = self.get_disbursement().status_history.order_by(
            "-created"
        )
        return context

    def form_valid(self, form):
        """Process the status change."""
        disbursement = self.get_disbursement()
        new_status = form.cleaned_data["status"]
        note = form.cleaned_data.get("note", "")

        # Change the status
        if disbursement.change_status(new_status, self.request.user, note):
            messages.success(
                self.request,
                _("Disbursement status changed to %(status)s")
                % {"status": disbursement.get_status_display()},
            )
        else:
            messages.warning(
                self.request,
                _("Disbursement status was already %(status)s")
                % {"status": disbursement.get_status_display()},
            )

        return redirect("apps.credits:disbursement_detail", pk=disbursement.pk)

    def get_success_url(self):
        """Return to disbursement detail page."""
        return reverse_lazy(
            "apps.credits:disbursement_detail",
            kwargs={"pk": self.get_disbursement().pk},
        )
