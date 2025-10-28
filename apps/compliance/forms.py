from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.compliance import models
from apps.partners import choices as partner_choices
from apps.partners import models as partner_models

User = get_user_model()


class ContributionForm(forms.ModelForm):
    """Form for creating and updating Contribution records."""

    class Meta:
        model = models.Contribution
        fields = [
            "partner",
            "amount",
            "period_year",
            "period_month",
            "due_date",
            "status",
        ]

        widgets = {
            "partner": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-placeholder": _("Select partner"),
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "period_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2020",
                    "max": "2030",
                }
            ),
            "period_month": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "12",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
        }

        labels = {
            "partner": _("Partner"),
            "amount": _("Amount"),
            "period_year": _("Period Year"),
            "period_month": _("Period Month"),
            "due_date": _("Due Date"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic querysets."""
        super().__init__(*args, **kwargs)

        # Filter partners to only active ones
        self.fields["partner"].queryset = partner_models.Partner.objects.filter(
            status=partner_choices.PartnerStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        # Set required fields
        self.fields["partner"].required = True
        self.fields["amount"].required = True
        self.fields["period_year"].required = True
        self.fields["period_month"].required = True
        self.fields["due_date"].required = True

    def clean_amount(self) -> Decimal:
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))
        return amount

    def clean_period_month(self) -> int:
        """Validate period month is between 1 and 12."""
        month = self.cleaned_data.get("period_month")
        if month is not None and not (1 <= month <= 12):
            raise ValidationError(_("Month must be between 1 and 12."))
        return month

    def clean(self) -> dict:
        """Perform cross-field validation."""
        cleaned_data = super().clean()
        partner = cleaned_data.get("partner")
        period_year = cleaned_data.get("period_year")
        period_month = cleaned_data.get("period_month")

        # Check for duplicate contribution for same partner and period
        if partner and period_year and period_month:
            existing = models.Contribution.objects.filter(
                partner=partner,
                period_year=period_year,
                period_month=period_month,
            )

            # Exclude current instance if updating
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    _("A contribution for this partner and period already exists.")
                )

        return cleaned_data


class SocialSecurityForm(forms.ModelForm):
    """Form for creating and updating SocialSecurity records."""

    class Meta:
        model = models.SocialSecurity
        fields = [
            "partner",
            "amount",
            "period_year",
            "period_month",
            "due_date",
            "status",
        ]

        widgets = {
            "partner": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-placeholder": _("Select partner"),
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "period_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2020",
                    "max": "2030",
                }
            ),
            "period_month": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "12",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
        }

        labels = {
            "partner": _("Partner"),
            "amount": _("Amount"),
            "period_year": _("Period Year"),
            "period_month": _("Period Month"),
            "due_date": _("Due Date"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic querysets."""
        super().__init__(*args, **kwargs)

        # Filter partners to only active ones
        self.fields["partner"].queryset = partner_models.Partner.objects.filter(
            status=partner_choices.PartnerStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        # Set required fields
        self.fields["partner"].required = True
        self.fields["amount"].required = True
        self.fields["period_year"].required = True
        self.fields["period_month"].required = True
        self.fields["due_date"].required = True

    def clean_amount(self) -> Decimal:
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))
        return amount

    def clean_period_month(self) -> int:
        """Validate period month is between 1 and 12."""
        month = self.cleaned_data.get("period_month")
        if month is not None and not (1 <= month <= 12):
            raise ValidationError(_("Month must be between 1 and 12."))
        return month

    def clean(self) -> dict:
        """Perform cross-field validation."""
        cleaned_data = super().clean()
        partner = cleaned_data.get("partner")
        period_year = cleaned_data.get("period_year")
        period_month = cleaned_data.get("period_month")

        # Check for duplicate social security for same partner and period
        if partner and period_year and period_month:
            existing = models.SocialSecurity.objects.filter(
                partner=partner,
                period_year=period_year,
                period_month=period_month,
            )

            # Exclude current instance if updating
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    _(
                        "A social security record for this partner and period already exists."
                    )
                )

        return cleaned_data


class PenaltyForm(forms.ModelForm):
    """Form for creating and updating Penalty records."""

    class Meta:
        model = models.Penalty
        fields = [
            "partner",
            "penalty_type",
            "amount",
            "description",
            "due_date",
            "status",
        ]

        widgets = {
            "partner": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-placeholder": _("Select partner"),
                }
            ),
            "penalty_type": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _(
                        "Description of the violation or reason for penalty"
                    ),
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
        }

        labels = {
            "partner": _("Partner"),
            "penalty_type": _("Penalty Type"),
            "amount": _("Amount"),
            "description": _("Description"),
            "due_date": _("Due Date"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic querysets."""
        super().__init__(*args, **kwargs)

        # Filter partners to only active ones
        self.fields["partner"].queryset = partner_models.Partner.objects.filter(
            status=partner_choices.PartnerStatus.ACTIVE
        ).order_by("first_name", "paternal_last_name")

        # Set required fields
        self.fields["partner"].required = True
        self.fields["penalty_type"].required = True
        self.fields["amount"].required = True
        self.fields["description"].required = True
        self.fields["due_date"].required = True

    def clean_amount(self) -> Decimal:
        """Validate amount is positive."""
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))
        return amount

    def clean_description(self) -> str:
        """Validate description is not empty."""
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise ValidationError(_("Description is required."))
        return description
