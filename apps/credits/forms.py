from django import forms
from django.utils.translation import gettext_lazy as _

from apps.credits import choices, models
from apps.partners import choices as partner_choices
from apps.partners import models as partner_models
from apps.team import choices as team_choices
from apps.team import models as team_models


class ProductTypeForm(forms.ModelForm):
    """Form for ProductType model."""

    class Meta:
        model = models.ProductType
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter product type name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter product type description"),
                    "rows": 4,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].help_text = _("Unique name for the product type")
        self.fields["description"].help_text = _(
            "Optional description of the product type"
        )
        self.fields["is_active"].help_text = _("Whether this product type is active")


class ProductForm(forms.ModelForm):
    """Form for Product model."""

    class Meta:
        model = models.Product
        fields = [
            "product_type",
            "name",
            "description",
            "min_amount",
            "max_amount",
            "min_interest_rate",
            "max_interest_rate",
            "interest_type",
            "min_term_duration",
            "max_term_duration",
            "payment_frequency",
            "min_delinquency_rate",
            "max_delinquency_rate",
            "is_active",
        ]
        widgets = {
            "product_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter product name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter product description"),
                    "rows": 4,
                }
            ),
            "min_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "max_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "min_interest_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "max_interest_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "interest_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "min_term_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("1"),
                    "min": "1",
                    "max": "600",
                }
            ),
            "max_term_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("1"),
                    "min": "1",
                    "max": "600",
                }
            ),
            "payment_frequency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "min_delinquency_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "max_delinquency_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "product_type": _("Product Type"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active product types
        self.fields["product_type"].queryset = models.ProductType.objects.filter(
            is_active=True
        )

        # Add help text
        self.fields["product_type"].help_text = _("Select the product type")
        self.fields["name"].help_text = _("Unique name for the product")
        self.fields["description"].help_text = _("Optional description of the product")
        self.fields["min_amount"].help_text = _("Minimum credit amount")
        self.fields["max_amount"].help_text = _("Maximum credit amount")
        self.fields["min_interest_rate"].help_text = _(
            "Minimum annual interest rate percentage"
        )
        self.fields["max_interest_rate"].help_text = _(
            "Maximum annual interest rate percentage"
        )
        self.fields["interest_type"].help_text = _("Type of interest rate")
        self.fields["min_term_duration"].help_text = _("Minimum duration in months")
        self.fields["max_term_duration"].help_text = _("Maximum duration in months")
        self.fields["payment_frequency"].help_text = _("How often payments are due")
        self.fields["min_delinquency_rate"].help_text = _(
            "Minimum delinquency rate percentage for overdue payments"
        )
        self.fields["max_delinquency_rate"].help_text = _(
            "Maximum delinquency rate percentage for overdue payments"
        )
        self.fields["is_active"].help_text = _("Whether this product is active")

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        min_amount = cleaned_data.get("min_amount")
        max_amount = cleaned_data.get("max_amount")
        min_interest_rate = cleaned_data.get("min_interest_rate")
        max_interest_rate = cleaned_data.get("max_interest_rate")
        min_term_duration = cleaned_data.get("min_term_duration")
        max_term_duration = cleaned_data.get("max_term_duration")
        min_delinquency_rate = cleaned_data.get("min_delinquency_rate")
        max_delinquency_rate = cleaned_data.get("max_delinquency_rate")

        # Validate amount ranges
        if min_amount and max_amount and min_amount > max_amount:
            raise forms.ValidationError(
                _("Minimum amount cannot be greater than maximum amount.")
            )

        # Validate interest rate ranges
        if (
            min_interest_rate is not None
            and max_interest_rate is not None
            and min_interest_rate > max_interest_rate
        ):
            raise forms.ValidationError(
                _("Minimum interest rate cannot be greater than maximum interest rate.")
            )

        # Validate term ranges
        if (
            min_term_duration
            and max_term_duration
            and min_term_duration > max_term_duration
        ):
            raise forms.ValidationError(
                _("Minimum term cannot be greater than maximum term.")
            )

        # Validate delinquency rate ranges
        if (
            min_delinquency_rate is not None
            and max_delinquency_rate is not None
            and min_delinquency_rate > max_delinquency_rate
        ):
            raise forms.ValidationError(
                _(
                    "Minimum delinquency rate cannot be greater than maximum delinquency rate."
                )
            )

        return cleaned_data


class CreditApplicationForm(forms.ModelForm):
    """Form for CreditApplication model."""

    class Meta:
        model = models.CreditApplication
        fields = [
            "partner",
            "product",
            "requested_amount",
            "proposed_interest_rate",
            "requested_term_duration",
            "possible_start_date",
            "proposed_delinquency_rate",
            "requested_payment_frequency",
            "estimated_payment_amount",
            "assigned_to",
        ]
        widgets = {
            "partner": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "product": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "requested_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "proposed_interest_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "requested_term_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("1"),
                    "min": "1",
                    "max": "600",
                }
            ),
            "possible_start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "proposed_delinquency_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "requested_payment_frequency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "estimated_payment_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "readonly": True,
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }
        labels = {
            "partner": _("Partner"),
            "product": _("Product"),
            "requested_amount": _("Requested Amount"),
            "proposed_interest_rate": _("Proposed Interest Rate (%)"),
            "requested_term_duration": _("Requested Term Duration"),
            "possible_start_date": _("Possible Start Date"),
            "proposed_delinquency_rate": _("Proposed Delinquency Rate (%)"),
            "requested_payment_frequency": _("Requested Payment Frequency"),
            "estimated_payment_amount": _("Estimated Payment Amount"),
            "assigned_to": _("Assigned To"),
        }

    def __init__(self, *args, **kwargs):
        # Extract custom parameters
        is_create = kwargs.pop("is_create", False)
        super().__init__(*args, **kwargs)

        # Filter querysets
        self.fields["partner"].queryset = partner_models.Partner.objects.filter(
            status=partner_choices.PartnerStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        self.fields["product"].queryset = (
            models.Product.objects.filter(is_active=True)
            .select_related("product_type")
            .order_by("product_type__name", "name")
        )

        # Configure assigned_to field

        self.fields["assigned_to"].queryset = team_models.Employee.objects.filter(
            status=team_choices.EmployeeStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        # Hide assigned_to field if not creating
        if not is_create:
            self.fields["assigned_to"].widget = forms.HiddenInput()

        self.fields[
            "requested_payment_frequency"
        ].initial = choices.PaymentFrequency.MONTHLY

        # Add empty labels
        self.fields["partner"].empty_label = _("Select a partner")
        self.fields["product"].empty_label = _("Select a product")
        self.fields["assigned_to"].empty_label = _("Select an employee")

        # Add help text
        self.fields["partner"].help_text = _("Partner who is applying for the credit")
        self.fields["product"].help_text = _("Product this application is for")
        self.fields["requested_amount"].help_text = _("Amount of credit requested")
        self.fields["proposed_interest_rate"].help_text = _(
            "Proposed annual interest rate percentage"
        )
        self.fields["requested_term_duration"].help_text = _(
            "Requested duration of the credit in months"
        )
        self.fields["possible_start_date"].help_text = _(
            "Estimated date when the credit could start"
        )
        self.fields["proposed_delinquency_rate"].help_text = _(
            "Proposed delinquency rate percentage for overdue payments"
        )
        self.fields["requested_payment_frequency"].help_text = _(
            "Requested frequency for payments"
        )
        self.fields["estimated_payment_amount"].help_text = _(
            "Estimated payment amount based on requested terms and frequency"
        )
        self.fields["assigned_to"].help_text = _(
            "Employee assigned to review this application"
        )

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        requested_amount = cleaned_data.get("requested_amount")
        proposed_interest_rate = cleaned_data.get("proposed_interest_rate")
        requested_term_duration = cleaned_data.get("requested_term_duration")
        proposed_delinquency_rate = cleaned_data.get("proposed_delinquency_rate")

        # Validate against product limits if product is selected
        if product and requested_amount:
            if requested_amount < product.min_amount:
                raise forms.ValidationError(
                    _(
                        f"Requested amount cannot be less than product minimum: ${product.min_amount}"
                    )
                )
            if requested_amount > product.max_amount:
                raise forms.ValidationError(
                    _(
                        f"Requested amount cannot be greater than product maximum: ${product.max_amount}"
                    )
                )

        if product and proposed_interest_rate is not None:
            if proposed_interest_rate < product.min_interest_rate:
                raise forms.ValidationError(
                    _(
                        f"Proposed interest rate cannot be less than product minimum: {product.min_interest_rate}%"
                    )
                )
            if proposed_interest_rate > product.max_interest_rate:
                raise forms.ValidationError(
                    _(
                        f"Proposed interest rate cannot be greater than product maximum: {product.max_interest_rate}%"
                    )
                )

        if product and requested_term_duration:
            if requested_term_duration < product.min_term_duration:
                raise forms.ValidationError(
                    _(
                        f"Requested term cannot be less than product minimum: {product.min_term_duration} months"
                    )
                )
            if requested_term_duration > product.max_term_duration:
                raise forms.ValidationError(
                    _(
                        f"Requested term cannot be greater than product maximum: {product.max_term_duration} months"
                    )
                )

        if product and proposed_delinquency_rate is not None:
            if proposed_delinquency_rate < product.min_delinquency_rate:
                raise forms.ValidationError(
                    _(
                        f"Proposed delinquency rate cannot be less than product minimum: {product.min_delinquency_rate}%"
                    )
                )
            if proposed_delinquency_rate > product.max_delinquency_rate:
                raise forms.ValidationError(
                    _(
                        f"Proposed delinquency rate cannot be greater than product maximum: {product.max_delinquency_rate}%"
                    )
                )

        return cleaned_data


class CreditApplicationStatusChangeForm(forms.Form):
    """Form for changing CreditApplication status."""

    status = forms.ChoiceField(
        label=_("New Status"),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text=_("Select the new status for the application."),
    )
    note = forms.CharField(
        label=_("Note"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _(
                    "Add a note about this status change (required for rejection)..."
                ),
            }
        ),
        required=False,
        help_text=_(
            "Note about the status change. Required when rejecting an application."
        ),
    )

    def __init__(self, *args, application=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if application and user:
            # Get possible status transitions for this application and user
            possible_statuses = application.get_possible_status_transitions(user)
            self.fields["status"].choices = [
                (status, dict(choices.CreditApplicationStatus.choices)[status])
                for status in possible_statuses
            ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        note = cleaned_data.get("note")

        # Require note when status is REJECTED
        if status == choices.CreditApplicationStatus.REJECTED:
            if not note or not note.strip():
                raise forms.ValidationError(
                    {"note": _("A note is required when rejecting an application.")}
                )

        return cleaned_data


class CreditForm(forms.ModelForm):
    """Form for Credit model."""

    class Meta:
        model = models.Credit
        fields = [
            "partner",
            "product",
            "amount",
            "interest_rate",
            "term_duration",
            "delinquency_rate",
            "payment_frequency",
            "payment_amount",
            "outstanding_balance",
            "notes",
        ]
        widgets = {
            "partner": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "product": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "interest_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "term_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("1"),
                    "min": "1",
                    "max": "600",
                }
            ),
            "delinquency_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "payment_frequency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "payment_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "outstanding_balance": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Additional notes about the credit"),
                    "rows": 4,
                }
            ),
        }
        labels = {
            "partner": _("Partner"),
            "product": _("Product"),
            "amount": _("Credit Amount"),
            "interest_rate": _("Interest Rate (%)"),
            "term_duration": _("Term Duration"),
            "delinquency_rate": _("Delinquency Rate (%)"),
            "payment_frequency": _("Payment Frequency"),
            "payment_amount": _("Payment Amount"),
            "outstanding_balance": _("Outstanding Balance"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter querysets
        self.fields["partner"].queryset = partner_models.Partner.objects.filter(
            status=partner_choices.PartnerStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        self.fields["product"].queryset = (
            models.Product.objects.filter(is_active=True)
            .select_related("product_type")
            .order_by("product_type__name", "name")
        )

        # Add empty labels
        self.fields["partner"].empty_label = _("Select a partner")
        self.fields["product"].empty_label = _("Select a product")

        # Add help text
        self.fields["partner"].help_text = _("Partner who requested the credit")
        self.fields["product"].help_text = _("Product this credit is based on")
        self.fields["amount"].help_text = _("Total amount of the credit")
        self.fields["interest_rate"].help_text = _("Annual interest rate percentage")
        self.fields["term_duration"].help_text = _("Duration of the credit")
        self.fields["delinquency_rate"].help_text = _(
            "Delinquency rate percentage for overdue payments"
        )
        self.fields["payment_frequency"].help_text = _(
            "How often payments are due for this credit"
        )
        self.fields["payment_amount"].help_text = _(
            "Calculated payment amount based on frequency"
        )
        self.fields["outstanding_balance"].help_text = _("Current outstanding balance")
        self.fields["notes"].help_text = _("Additional notes about the credit")

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        amount = cleaned_data.get("amount")
        interest_rate = cleaned_data.get("interest_rate")
        term_duration = cleaned_data.get("term_duration")
        delinquency_rate = cleaned_data.get("delinquency_rate")

        # Validate against product limits if product is selected
        if product and amount:
            if amount < product.min_amount:
                raise forms.ValidationError(
                    _(
                        f"Credit amount cannot be less than product minimum: ${product.min_amount}"
                    )
                )
            if amount > product.max_amount:
                raise forms.ValidationError(
                    _(
                        f"Credit amount cannot be greater than product maximum: ${product.max_amount}"
                    )
                )

        if product and interest_rate is not None:
            if interest_rate < product.min_interest_rate:
                raise forms.ValidationError(
                    _(
                        f"Interest rate cannot be less than product minimum: {product.min_interest_rate}%"
                    )
                )
            if interest_rate > product.max_interest_rate:
                raise forms.ValidationError(
                    _(
                        f"Interest rate cannot be greater than product maximum: {product.max_interest_rate}%"
                    )
                )

        if product and term_duration:
            if term_duration < product.min_term_duration:
                raise forms.ValidationError(
                    _(
                        f"Term duration cannot be less than product minimum: {product.min_term_duration} months"
                    )
                )
            if term_duration > product.max_term_duration:
                raise forms.ValidationError(
                    _(
                        f"Term duration cannot be greater than product maximum: {product.max_term_duration} months"
                    )
                )

        if product and delinquency_rate is not None:
            if delinquency_rate < product.min_delinquency_rate:
                raise forms.ValidationError(
                    _(
                        f"Delinquency rate cannot be less than product minimum: {product.min_delinquency_rate}%"
                    )
                )
            if delinquency_rate > product.max_delinquency_rate:
                raise forms.ValidationError(
                    _(
                        f"Delinquency rate cannot be greater than product maximum: {product.max_delinquency_rate}%"
                    )
                )

        return cleaned_data


class CreditRescheduleRequestForm(forms.ModelForm):
    """Form for CreditRescheduleRequest model."""

    class Meta:
        model = models.CreditRescheduleRequest
        fields = [
            "credit",
            "requested_term_extension",
            "requested_interest_rate_adjustment",
            "requested_start_date",
            "reason",
            "status",
            "notes",
        ]
        widgets = {
            "credit": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "requested_term_extension": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Periods"),
                    "min": "1",
                    "max": "60",
                }
            ),
            "requested_interest_rate_adjustment": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "-5.00",
                    "max": "5.00",
                }
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _(
                        "Explain the reason for requesting the reschedule"
                    ),
                    "rows": 4,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "requested_start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Additional notes about the reschedule request"),
                    "rows": 3,
                }
            ),
        }
        labels = {
            "credit": _("Credit"),
            "requested_term_extension": _("Requested Term Extension"),
            "requested_interest_rate_adjustment": _(
                "Requested Interest Rate Adjustment (%)"
            ),
            "requested_start_date": _("Requested Start Date"),
            "reason": _("Reason for Reschedule"),
            "status": _("Status"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        # Extract custom parameters
        user = kwargs.pop("user", None)
        is_create = kwargs.pop("is_create", False)
        super().__init__(*args, **kwargs)

        # Configure status field based on operation and permissions
        self._configure_status_field(user, is_create)

        # Filter querysets - only show active credits
        self.fields["credit"].queryset = (
            models.Credit.objects.filter(
                status__in=[
                    choices.CreditStatus.ACTIVE,
                    choices.CreditStatus.APPROVED,
                ]
            )
            .select_related("partner", "product")
            .order_by("-created")
        )

        # Add empty labels
        self.fields["credit"].empty_label = _("Select a credit")

        # Add help text
        self.fields["credit"].help_text = _(
            "Credit this reschedule request is for. Select a credit to see product limits."
        )
        self.fields["requested_term_extension"].help_text = _(
            "Number of periods to extend the loan term. The final term duration cannot exceed the product's maximum term limit."
        )
        self.fields["requested_interest_rate_adjustment"].help_text = _(
            "Percentage adjustment to the interest rate (positive to increase, negative to decrease). "
            "The final interest rate must be within the product's interest rate range."
        )
        self.fields["reason"].help_text = _("Reason for requesting the loan reschedule")
        self.fields["status"].help_text = _("Current status of the reschedule request")
        self.fields["notes"].help_text = _(
            "Additional notes about the reschedule request"
        )

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        credit = cleaned_data.get("credit")
        requested_term_extension = cleaned_data.get("requested_term_extension")
        requested_interest_rate_adjustment = cleaned_data.get(
            "requested_interest_rate_adjustment"
        )

        # Ensure at least one adjustment is requested
        if not requested_term_extension and not requested_interest_rate_adjustment:
            raise forms.ValidationError(
                _(
                    "You must request at least one type of adjustment (term extension or interest rate change)."
                )
            )

        # Validate against product limits if credit is selected
        if credit and credit.product:
            product = credit.product

            # Validate term extension
            if requested_term_extension:
                if requested_term_extension > product.max_term_duration:
                    raise forms.ValidationError(
                        {
                            "requested_term_extension": _(
                                f"Term extension would result in {requested_term_extension} months, "
                                f"which exceeds the product maximum of {product.max_term_duration} months."
                            )
                        }
                    )

            # Validate interest rate adjustment
            if requested_interest_rate_adjustment:
                # Calculate new interest rate
                new_interest_rate = requested_interest_rate_adjustment

                if new_interest_rate < product.min_interest_rate:
                    raise forms.ValidationError(
                        {
                            "requested_interest_rate_adjustment": _(
                                f"Interest rate adjustment would result in {new_interest_rate}%, "
                                f"which is below the product minimum of {product.min_interest_rate}%."
                            )
                        }
                    )

                if new_interest_rate > product.max_interest_rate:
                    raise forms.ValidationError(
                        {
                            "requested_interest_rate_adjustment": _(
                                f"Interest rate adjustment would result in {new_interest_rate}%, "
                                f"which exceeds the product maximum of {product.max_interest_rate}%."
                            )
                        }
                    )

        return cleaned_data

    def clean_requested_term_extension(self):
        """Validate requested term extension against product limits."""
        requested_term_extension = self.cleaned_data.get("requested_term_extension")
        credit = self.cleaned_data.get("credit")

        if requested_term_extension and credit and credit.product:
            product = credit.product
            new_term_duration = requested_term_extension

            if new_term_duration > product.max_term_duration:
                raise forms.ValidationError(
                    _(
                        f"Term extension would result in {new_term_duration} months, "
                        f"which exceeds the product maximum of {product.max_term_duration} months. "
                        f"Maximum extension allowed: {product.max_term_duration - credit.term_duration} months."
                    )
                )

        return requested_term_extension

    def clean_requested_interest_rate_adjustment(self):
        """Validate requested interest rate adjustment against product limits."""
        requested_interest_rate_adjustment = self.cleaned_data.get(
            "requested_interest_rate_adjustment"
        )
        credit = self.cleaned_data.get("credit")

        if requested_interest_rate_adjustment and credit and credit.product:
            product = credit.product
            new_interest_rate = requested_interest_rate_adjustment

            if new_interest_rate < product.min_interest_rate:
                max_decrease = credit.interest_rate - product.min_interest_rate
                raise forms.ValidationError(
                    _(
                        f"Interest rate adjustment would result in {new_interest_rate}%, "
                        f"which is below the product minimum of {product.min_interest_rate}%. "
                        f"Maximum decrease allowed: {max_decrease}%."
                    )
                )

            if new_interest_rate > product.max_interest_rate:
                max_increase = product.max_interest_rate - credit.interest_rate
                raise forms.ValidationError(
                    _(
                        f"Interest rate adjustment would result in {new_interest_rate}%, "
                        f"which exceeds the product maximum of {product.max_interest_rate}%. "
                        f"Maximum increase allowed: {max_increase}%."
                    )
                )

        return requested_interest_rate_adjustment

    def _configure_status_field(self, user, is_create: bool):
        """Configure status field choices based on operation type and user permissions."""
        if is_create:
            # For new requests, only allow PENDING status
            self.fields["status"].choices = [
                (
                    choices.RescheduleRequestStatus.PENDING,
                    choices.RescheduleRequestStatus.PENDING.label,
                )
            ]
            self.fields["status"].initial = choices.RescheduleRequestStatus.PENDING
        else:
            # For updates, filter status choices based on permissions
            available_choices = []

            # Always include current status if instance exists
            if self.instance and self.instance.status:
                current_status = self.instance.status
                current_label = dict(choices.RescheduleRequestStatus.choices)[
                    current_status
                ]
                available_choices.append((current_status, current_label))

            # Add PENDING - everyone can set back to pending
            if choices.RescheduleRequestStatus.PENDING not in [
                choice[0] for choice in available_choices
            ]:
                available_choices.append(
                    (
                        choices.RescheduleRequestStatus.PENDING,
                        choices.RescheduleRequestStatus.PENDING.label,
                    )
                )

            # Add status transitions based on permissions
            if user:
                # Users with credit management permissions can approve/reject
                if user.has_perm("credits.change_credit"):
                    statuses_to_add = [
                        choices.RescheduleRequestStatus.APPROVED,
                        choices.RescheduleRequestStatus.REJECTED,
                        choices.RescheduleRequestStatus.CANCELLED,
                    ]
                    for status in statuses_to_add:
                        if status not in [choice[0] for choice in available_choices]:
                            available_choices.append((status, status.label))

            # Set the filtered choices
            self.fields["status"].choices = available_choices


class CreditStatusChangeForm(forms.Form):
    """Form for changing Credit status."""

    status = forms.ChoiceField(
        label=_("New Status"),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text=_("Select the new status for the credit."),
    )
    note = forms.CharField(
        label=_("Note"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _(
                    "Add a note about this status change (required for rejection)..."
                ),
            }
        ),
        required=False,
        help_text=_("Note about the status change. Required when rejecting a credit."),
    )

    def __init__(self, *args, credit=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if credit and user:
            # Get possible status transitions for this credit and user
            possible_statuses = credit.get_possible_status_transitions(user)
            self.fields["status"].choices = [
                (status, dict(choices.CreditStatus.choices)[status])
                for status in possible_statuses
            ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        note = cleaned_data.get("note")

        # Require note when status is REJECTED
        if status == choices.CreditStatus.REJECTED:
            if not note or not note.strip():
                raise forms.ValidationError(
                    {"note": _("A note is required when rejecting a credit.")}
                )

        return cleaned_data


class CreditRefinanceRequestForm(forms.ModelForm):
    """Form for CreditRefinanceRequest model."""

    class Meta:
        model = models.CreditRefinanceRequest
        fields = [
            "credit",
            "previous_outstanding_balance",
            "previous_term_remaining",
            "new_payment_frequency",
            "new_term_duration",
            "new_interest_rate",
            "new_delinquency_rate",
            "additional_amount",
            "start_date",
            "reason",
            "status",
        ]
        widgets = {
            "credit": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "previous_outstanding_balance": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                    "readonly": True,
                }
            ),
            "previous_term_remaining": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("1"),
                    "min": "1",
                    "readonly": True,
                }
            ),
            "new_payment_frequency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "new_term_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Months"),
                    "min": "1",
                    "max": "600",
                }
            ),
            "new_interest_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "new_delinquency_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "additional_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Explain the reason for the refinancing"),
                    "rows": 4,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }
        labels = {
            "credit": _("Credit"),
            "previous_outstanding_balance": _("Previous Outstanding Balance"),
            "previous_term_remaining": _("Previous Term Remaining"),
            "new_payment_frequency": _("New Payment Frequency"),
            "new_term_duration": _("New Term Duration"),
            "new_interest_rate": _("New Interest Rate (%)"),
            "new_delinquency_rate": _("New Delinquency Rate (%)"),
            "additional_amount": _("Additional Amount"),
            "start_date": _("Start Date"),
            "reason": _("Reason"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with custom configurations."""
        # Extract custom parameters
        user = kwargs.pop("user", None)
        is_create = kwargs.pop("is_create", False)
        super().__init__(*args, **kwargs)

        # Configure status field based on operation and permissions
        self._configure_status_field(user, is_create)

        # Filter querysets - only show active credits
        self.fields["credit"].queryset = (
            models.Credit.objects.filter(
                status__in=[
                    choices.CreditStatus.ACTIVE,
                    choices.CreditStatus.APPROVED,
                ]
            )
            .select_related("partner", "product")
            .order_by("-created")
        )

        # Add empty labels
        self.fields["credit"].empty_label = _("Select a credit")

        # Add help text
        self.fields["credit"].help_text = _("Credit being refinanced")
        self.fields["previous_outstanding_balance"].help_text = _(
            "Outstanding balance before refinancing"
        )
        self.fields["previous_term_remaining"].help_text = _(
            "Remaining months before refinancing"
        )
        self.fields["new_payment_frequency"].help_text = _("New payment frequency")
        self.fields["new_term_duration"].help_text = _("New total duration in months")
        self.fields["new_interest_rate"].help_text = _("New interest rate percentage")
        self.fields["new_delinquency_rate"].help_text = _(
            "New delinquency rate percentage for overdue payments"
        )
        self.fields["additional_amount"].help_text = _(
            "Any additional amount added to the outstanding balance"
        )
        self.fields["start_date"].help_text = _("Start date for new installments")
        self.fields["reason"].help_text = _("Reason for the refinancing")
        self.fields["status"].help_text = _("Current status of the refinance request")

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        credit = cleaned_data.get("credit")
        new_term_duration = cleaned_data.get("new_term_duration")
        new_interest_rate = cleaned_data.get("new_interest_rate")
        new_delinquency_rate = cleaned_data.get("new_delinquency_rate")

        # Validate against product limits if credit is selected
        if credit and credit.product:
            product = credit.product

            # Validate term duration
            if new_term_duration:
                if new_term_duration < product.min_term_duration:
                    raise forms.ValidationError(
                        {
                            "new_term_duration": _(
                                f"New term duration cannot be less than product minimum: {product.min_term_duration} months"
                            )
                        }
                    )
                if new_term_duration > product.max_term_duration:
                    raise forms.ValidationError(
                        {
                            "new_term_duration": _(
                                f"New term duration cannot exceed product maximum: {product.max_term_duration} months"
                            )
                        }
                    )

            # Validate interest rate
            if new_interest_rate is not None:
                if new_interest_rate < product.min_interest_rate:
                    raise forms.ValidationError(
                        {
                            "new_interest_rate": _(
                                f"New interest rate cannot be less than product minimum: {product.min_interest_rate}%"
                            )
                        }
                    )
                if new_interest_rate > product.max_interest_rate:
                    raise forms.ValidationError(
                        {
                            "new_interest_rate": _(
                                f"New interest rate cannot exceed product maximum: {product.max_interest_rate}%"
                            )
                        }
                    )

            # Validate delinquency rate
            if new_delinquency_rate is not None:
                if new_delinquency_rate < product.min_delinquency_rate:
                    raise forms.ValidationError(
                        {
                            "new_delinquency_rate": _(
                                f"New delinquency rate cannot be less than product minimum: {product.min_delinquency_rate}%"
                            )
                        }
                    )
                if new_delinquency_rate > product.max_delinquency_rate:
                    raise forms.ValidationError(
                        {
                            "new_delinquency_rate": _(
                                f"New delinquency rate cannot exceed product maximum: {product.max_delinquency_rate}%"
                            )
                        }
                    )

        return cleaned_data

    def _configure_status_field(self, user, is_create: bool):
        """Configure status field choices based on operation type and user permissions."""
        if is_create:
            # For new requests, only allow PENDING status
            self.fields["status"].choices = [
                (
                    choices.RefinanceRequestStatus.PENDING,
                    choices.RefinanceRequestStatus.PENDING.label,
                )
            ]
            self.fields["status"].initial = choices.RefinanceRequestStatus.PENDING
        else:
            # For updates, filter status choices based on permissions
            available_choices = []

            # Always include current status if instance exists
            if self.instance and self.instance.status:
                current_status = self.instance.status
                current_label = dict(choices.RefinanceRequestStatus.choices)[
                    current_status
                ]
                available_choices.append((current_status, current_label))

            # Add PENDING - everyone can set back to pending
            if choices.RefinanceRequestStatus.PENDING not in [
                choice[0] for choice in available_choices
            ]:
                available_choices.append(
                    (
                        choices.RefinanceRequestStatus.PENDING,
                        choices.RefinanceRequestStatus.PENDING.label,
                    )
                )

            # Add status transitions based on permissions
            if user:
                # Users with credit management permissions can approve/reject
                if user.has_perm("credits.change_credit"):
                    statuses_to_add = [
                        choices.RefinanceRequestStatus.APPROVED,
                        choices.RefinanceRequestStatus.REJECTED,
                        choices.RefinanceRequestStatus.CANCELLED,
                    ]
                    for status in statuses_to_add:
                        if status not in [choice[0] for choice in available_choices]:
                            available_choices.append((status, status.label))

            # Set the filtered choices
            self.fields["status"].choices = available_choices


class CreditDisbursementForm(forms.ModelForm):
    """Form for CreditDisbursement model."""

    class Meta:
        model = models.CreditDisbursement
        fields = [
            "credit",
            "disbursement_amount",
            "scheduled_date",
            "disbursement_method",
            "bank_name",
            "account_number",
            "account_holder_name",
            "check_number",
            "reference_number",
            "receipt_document",
        ]
        widgets = {
            "credit": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "disbursement_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("0.00"),
                    "step": "0.01",
                    "min": "0.01",
                    "readonly": True,
                }
            ),
            "scheduled_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "disbursement_method": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "bank_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter bank name"),
                }
            ),
            "account_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter account number"),
                }
            ),
            "account_holder_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter account holder name"),
                }
            ),
            "check_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter check number"),
                }
            ),
            "reference_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter reference number"),
                }
            ),
            "receipt_document": forms.FileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with custom configurations."""
        super().__init__(*args, **kwargs)

        # Filter querysets - only show approved or active credits
        self.fields["credit"].queryset = (
            models.Credit.objects.filter(
                status__in=[
                    choices.CreditStatus.APPROVED,
                    choices.CreditStatus.ACTIVE,
                ]
            )
            .select_related("partner", "product")
            .order_by("-created")
        )

        # Add empty labels
        self.fields["credit"].empty_label = _("Select a credit")

        # If editing an existing disbursement, set amount to credit amount
        if self.instance and self.instance.pk and self.instance.credit:
            self.initial["disbursement_amount"] = self.instance.credit.amount

        # Add help text
        self.fields["credit"].help_text = _("Credit being disbursed")
        self.fields["disbursement_amount"].help_text = _(
            "Amount will be automatically filled from the selected credit"
        )
        self.fields["scheduled_date"].help_text = _(
            "Date when the disbursement is scheduled"
        )
        self.fields["disbursement_method"].help_text = _("Method used for disbursement")
        self.fields["bank_name"].help_text = _("Bank name (required for bank transfer)")
        self.fields["account_number"].help_text = _(
            "Account number (required for bank transfer)"
        )
        self.fields["account_holder_name"].help_text = _(
            "Account holder name (required for bank transfer)"
        )
        self.fields["check_number"].help_text = _(
            "Check number (required if method is check)"
        )
        self.fields["reference_number"].help_text = _("Transaction reference number")
        self.fields["receipt_document"].help_text = _(
            "Upload receipt or proof of disbursement"
        )

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()
        credit = cleaned_data.get("credit")
        disbursement_method = cleaned_data.get("disbursement_method")
        bank_name = cleaned_data.get("bank_name")
        account_number = cleaned_data.get("account_number")
        check_number = cleaned_data.get("check_number")

        # Automatically set disbursement_amount to credit amount
        if credit:
            cleaned_data["disbursement_amount"] = credit.amount

        # Validate bank transfer requirements
        if disbursement_method == choices.DisbursementMethod.BANK_TRANSFER:
            if not bank_name:
                raise forms.ValidationError(
                    {"bank_name": _("Bank name is required for bank transfers")}
                )
            if not account_number:
                raise forms.ValidationError(
                    {
                        "account_number": _(
                            "Account number is required for bank transfers"
                        )
                    }
                )

        # Validate check requirements
        if disbursement_method == choices.DisbursementMethod.CHECK:
            if not check_number:
                raise forms.ValidationError(
                    {"check_number": _("Check number is required for check payments")}
                )

        return cleaned_data


class CreditDisbursementStatusChangeForm(forms.Form):
    """Form for changing the status of a CreditDisbursement."""

    status = forms.ChoiceField(
        label=_("Status"),
        choices=choices.DisbursementStatus.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    note = forms.CharField(
        label=_("Note"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Optional note about the status change"),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with disbursement instance and user."""
        self.disbursement = kwargs.pop("disbursement", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set initial status value
        if self.disbursement:
            self.fields["status"].initial = self.disbursement.status

        # Configure available statuses based on current status and permissions
        self._configure_status_choices()

    def _configure_status_choices(self):
        """Configure available status choices based on current status and permissions."""
        if not self.disbursement:
            return

        current_status = self.disbursement.status
        available_statuses = []

        # Define status transitions
        status_transitions = {
            choices.DisbursementStatus.PENDING: [
                choices.DisbursementStatus.APPROVED,
                choices.DisbursementStatus.CANCELLED,
            ],
            choices.DisbursementStatus.APPROVED: [
                choices.DisbursementStatus.PROCESSING,
                choices.DisbursementStatus.CANCELLED,
            ],
            choices.DisbursementStatus.PROCESSING: [
                choices.DisbursementStatus.COMPLETED,
                choices.DisbursementStatus.FAILED,
            ],
            choices.DisbursementStatus.FAILED: [
                choices.DisbursementStatus.PROCESSING,
                choices.DisbursementStatus.CANCELLED,
            ],
        }

        # Get possible transitions
        possible_transitions = status_transitions.get(current_status, [])

        # Add current status
        available_statuses.append(
            (
                current_status,
                dict(choices.DisbursementStatus.choices)[current_status],
            )
        )

        # Add possible transitions based on permissions
        for status in possible_transitions:
            if self.user:
                # Check permissions
                if status == choices.DisbursementStatus.APPROVED:
                    if not self.user.has_perm("credits.approve_creditdisbursement"):
                        continue
                elif status in [
                    choices.DisbursementStatus.PROCESSING,
                    choices.DisbursementStatus.COMPLETED,
                    choices.DisbursementStatus.FAILED,
                ]:
                    if not self.user.has_perm("credits.process_creditdisbursement"):
                        continue

            available_statuses.append(
                (status, dict(choices.DisbursementStatus.choices)[status])
            )

        # Set filtered choices
        self.fields["status"].choices = available_statuses

    def clean_status(self):
        """Validate that the status change is allowed."""
        new_status = self.cleaned_data.get("status")

        if not self.disbursement:
            raise forms.ValidationError(_("Disbursement instance is required"))

        # Prevent changing status of completed or cancelled disbursements
        if self.disbursement.status in [
            choices.DisbursementStatus.COMPLETED,
            choices.DisbursementStatus.CANCELLED,
        ]:
            if new_status != self.disbursement.status:
                raise forms.ValidationError(
                    _("Cannot change status of completed or cancelled disbursements")
                )

        return new_status
