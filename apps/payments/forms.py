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


class PaymentReceiptForm(forms.ModelForm):
    """Form for creating and editing payment receipts."""

    class Meta:
        model = models.PaymentReceipt
        fields = [
            "partner",
            "payment",
            "receipt_file",
            "amount",
            "payment_date",
            "notes",
        ]
        widgets = {
            "partner": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "payment": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "receipt_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "payment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic queryset filtering."""
        super().__init__(*args, **kwargs)

        # Optimize partner queryset
        self.fields["partner"].queryset = Partner.objects.select_related().order_by(
            "first_name"
        )

        # Make payment field optional
        self.fields["payment"].required = False

        # Filter payments if editing
        if self.instance.pk and self.instance.partner:
            self.fields["payment"].queryset = models.Payment.objects.filter(
                partner=self.instance.partner
            ).order_by("-created")
        else:
            self.fields["payment"].queryset = models.Payment.objects.none()

    def clean_receipt_file(self):
        """Validate receipt file format and size."""
        receipt_file = self.cleaned_data.get("receipt_file")

        if receipt_file:
            # Validate file extension
            allowed_extensions = ["pdf", "jpg", "jpeg", "png"]
            file_extension = receipt_file.name.split(".")[-1].lower()

            if file_extension not in allowed_extensions:
                raise ValidationError(
                    _(
                        "Invalid file format. Allowed formats: PDF, JPG, JPEG, PNG"
                    )
                )

            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if receipt_file.size > max_size:
                raise ValidationError(_("File size must not exceed 5MB."))

        return receipt_file

    def clean_amount(self):
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")

        if amount and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))

        return amount


class MagicPaymentLinkForm(forms.Form):
    """Form for creating Magic Payment Links by partner document number."""

    document_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Ingrese el DNI del cliente..."),
                "autofocus": True,
            }
        ),
        label=_("DNI del Cliente"),
        help_text=_("Documento de identidad del socio"),
    )

    name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Ej: Pago de deudas pendientes - Enero 2025"),
            }
        ),
        label=_("Título del Magic Link"),
        help_text=_("Se generará automáticamente si se deja vacío"),
    )

    hours_to_expire = forms.IntegerField(
        initial=48,
        min_value=1,
        max_value=168,  # 7 días máximo
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "max": "168",
            }
        ),
        label=_("Horas de Expiración"),
        help_text=_("El link expirará en estas horas (máximo 7 días)"),
    )

    include_upcoming = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Incluir deudas por vencer"),
        help_text=_("Además de las vencidas, incluir deudas próximas a vencer"),
    )

    def clean_document_number(self):
        """Validate that partner exists."""
        document_number = self.cleaned_data.get("document_number")

        if document_number:
            try:
                Partner.objects.get(document_number=document_number)
            except Partner.DoesNotExist:
                raise ValidationError(
                    _("No se encontró un socio con el DNI %(document)s"),
                    params={"document": document_number},
                )

        return document_number
