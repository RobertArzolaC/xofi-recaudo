from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.team import models
from apps.users import models as user_models


class AreaForm(forms.ModelForm):
    """Form for Area model."""

    class Meta:
        model = models.Area
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter area name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Enter area description"),
                }
            ),
        }


class PositionForm(forms.ModelForm):
    """Form for Position model."""

    class Meta:
        model = models.Position
        fields = ["name", "description", "area"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter position name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Enter position description"),
                }
            ),
            "area": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].help_text = _("Select the area for this position.")


class EmployeeForm(forms.ModelForm):
    """Form for Employee model."""

    class Meta:
        model = models.Employee
        fields = [
            "email",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "document_type",
            "document_number",
            "gender",
            "birth_date",
            "phone",
            "position",
            "agency",
            "status",
            "address",
            "zip_code",
            "country",
            "region",
            "subregion",
            "city",
        ]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter email address"),
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter first name"),
                }
            ),
            "paternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter paternal last name"),
                }
            ),
            "maternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter maternal last name"),
                }
            ),
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "document_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter document number"),
                }
            ),
            "gender": forms.Select(
                attrs={"class": "form-select"},
            ),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter phone number"),
                }
            ),
            "position": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "agency": autocomplete.ModelSelect2(
                url="apps.customers:agency-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select agency..."),
                },
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter address"),
                }
            ),
            "zip_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter zip code"),
                }
            ),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-placeholder": _("Select country..."),
                },
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-placeholder": _("Select region..."),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-placeholder": _("Select subregion..."),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-placeholder": _("Select city..."),
                },
            ),
        }
        labels = {
            "first_name": _("First Name"),
            "paternal_last_name": _("Paternal Last Name"),
            "maternal_last_name": _("Maternal Last Name"),
            "document_type": _("Document Type"),
            "document_number": _("Document Number"),
            "birth_date": _("Birth Date"),
            "zip_code": _("Zip Code"),
            "position": _("Position"),
            "agency": _("Agency"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("District"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make certain fields required
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["paternal_last_name"].required = True
        self.fields["document_number"].required = True
        self.fields["position"].required = True

        # Set help texts
        self.fields["email"].help_text = _(
            "Email address for the employee. A user account will be created automatically."
        )
        self.fields["position"].help_text = _("Select the position for this employee.")
        self.fields["status"].help_text = _("Current employment status.")

        # Optimize querysets for performance
        self.fields["position"].queryset = models.Position.objects.select_related(
            "area"
        )

    def clean_email(self):
        """
        Validate that the email is not already registered for another User or Employee.

        Returns:
            str: The cleaned email if valid

        Raises:
            ValidationError: If email is already in use
        """
        email = self.cleaned_data.get("email")
        if not email:
            return email

        # Check if email is already used by another User
        existing_user = user_models.User.objects.filter(email=email).first()
        if existing_user:
            # If editing an existing employee, allow the same email if it belongs to this employee's user
            if self.instance.pk and self.instance.user == existing_user:
                return email
            else:
                raise ValidationError(
                    _("This email is already registered for another user account.")
                )

        # Check if email is already used by another Employee
        existing_employee = (
            models.Employee.objects.filter(email=email)
            .exclude(pk=self.instance.pk if self.instance.pk else None)
            .first()
        )
        if existing_employee:
            raise ValidationError(
                _("This email is already registered for another employee.")
            )

        return email
