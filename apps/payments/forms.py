from decimal import Decimal
from typing import Any, Dict

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.partners.models import Partner
from apps.payments import choices, models


class PaymentForm(forms.ModelForm):
    """Form for creating and editing payments."""

    class Meta:
        model = models.Payment
        fields = [
            "partner",
            "payment_number",
            "payment_date",
            "amount",
            "payment_method",
            "reference_number",
            "status",
            "notes",
        ]
        widgets = {
            "partner": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "payment_number": forms.TextInput(attrs={"class": "form-control"}),
            "payment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference_number": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "partner": _("Partner"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic partner selection."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.fields["partner"].queryset = Partner.objects.select_related().order_by(
            "first_name"
        )

        # Set default values for new payments
        if not self.instance.pk:
            self.fields["status"].initial = choices.PaymentStatus.PAID

    def clean(self) -> Dict[str, Any]:
        """Validate form data."""
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        payment_date = cleaned_data.get("payment_date")

        # Validate amount
        if amount and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))

        # Validate payment date is required
        if not payment_date:
            raise ValidationError(_("Payment date is required."))

        return cleaned_data


class PaymentConceptAllocationForm(forms.ModelForm):
    """Form for allocating payments to concepts."""

    class Meta:
        model = models.PaymentConceptAllocation
        fields = [
            "payment",
            "amount_applied",
            "allocation_type",
            "notes",
        ]
        widgets = {
            "payment": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "amount_applied": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "allocation_type": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize allocation form."""
        partner = kwargs.pop("partner", None)
        super().__init__(*args, **kwargs)

        # Filter payments by partner if provided
        if partner:
            self.fields["payment"].queryset = models.Payment.objects.filter(
                partner=partner,
                status=choices.PaymentStatus.PAID,
            ).order_by("-created")
        else:
            self.fields["payment"].queryset = models.Payment.objects.filter(
                status=choices.PaymentStatus.PAID
            ).order_by("-created")

    def clean(self) -> Dict[str, Any]:
        """Validate allocation data."""
        cleaned_data = super().clean()
        payment = cleaned_data.get("payment")
        amount_applied = cleaned_data.get("amount_applied")

        if payment and amount_applied:
            # Check if payment has enough unallocated amount
            if amount_applied > payment.unallocated_amount:
                raise ValidationError(
                    _(
                        "Amount to allocate ({}) exceeds unallocated amount ({})."
                    ).format(amount_applied, payment.unallocated_amount)
                )

        return cleaned_data


class QuickPaymentForm(forms.Form):
    """Quick form for creating and processing payments."""

    partner = forms.ModelChoiceField(
        queryset=Partner.objects.all(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "data-control": "select2",
                "id": "id_quick_partner",
            }
        ),
        label=_("Partner"),
    )

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
            }
        ),
        label=_("Amount"),
    )

    payment_method = forms.ChoiceField(
        choices=choices.PaymentMethod.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Payment Method"),
        initial=choices.PaymentMethod.CASH,
    )

    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label=_("Reference Number"),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
            }
        ),
        label=_("Notes"),
    )

    auto_allocate = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Auto-allocate to pending debts"),
    )

    def __init__(self, *args, **kwargs):
        """Initialize quick payment form."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.fields["partner"].queryset = Partner.objects.order_by("name")


class PartnerPaymentForm(forms.Form):
    """
    Form for partners to make online payments.

    This form is used by partners in their dashboard to create payments
    for different concepts (installments, penalties, contributions, etc.).
    """

    concept_type = forms.ChoiceField(
        choices=choices.PaymentConcept.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_concept_type",
            }
        ),
        label=_("Payment Concept"),
        help_text=_("Select the type of payment you want to make"),
    )

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "id": "id_amount",
                "readonly": "readonly",
            }
        ),
        label=_("Amount"),
        help_text=_("Amount will be calculated based on selected debts"),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "id": "id_notes",
            }
        ),
        label=_("Notes"),
        help_text=_("Optional notes about this payment"),
    )

    # Hidden field to store Culqi token
    culqi_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(attrs={"id": "culqi_token"}),
        label=_("Payment Token"),
    )

    # Hidden field to store selected allocations as JSON
    allocations_data = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "allocations_data"}),
        label=_("Allocations Data"),
    )

    def clean_amount(self) -> Decimal:
        """Validate payment amount."""
        amount = self.cleaned_data.get("amount")

        if amount and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))

        return amount

    def clean_culqi_token(self) -> str:
        """Validate Culqi token."""
        token = self.cleaned_data.get("culqi_token")

        if not token:
            raise ValidationError(
                _("Payment token is required. Please complete the payment form.")
            )

        return token

    def clean(self) -> Dict[str, Any]:
        """Validate form data."""
        cleaned_data = super().clean()

        # Validate amount
        amount = cleaned_data.get("amount")
        if not amount or amount <= 0:
            raise ValidationError(_("Please enter a valid payment amount."))

        return cleaned_data
