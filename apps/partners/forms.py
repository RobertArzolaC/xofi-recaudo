from cities_light.models import Country
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.partners import choices, models
from apps.team import choices as team_choices


class ApplicantForm(forms.ModelForm):
    """Form for creating and editing Applicant instances."""

    class Meta:
        model = models.Applicant
        fields = [
            "external_id",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "document_type",
            "document_number",
            "gender",
            "birth_date",
            "phone",
            "email",
            "address",
            "country",
            "region",
            "subregion",
            "city",
            "agency",
            "status",
        ]
        widgets = {
            "external_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("External ID"),
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("First name"),
                }
            ),
            "paternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Paternal last name"),
                }
            ),
            "maternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Maternal last name"),
                }
            ),
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "document_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Document number"),
                }
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "birth_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Phone number"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Email address"),
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Address"),
                }
            ),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select country..."),
                },
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-placeholder": _("Select region..."),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select subregion..."),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select city..."),
                },
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
        }
        labels = {
            "external_id": _("External ID"),
            "first_name": _("First Name"),
            "paternal_last_name": _("Paternal Last Name"),
            "maternal_last_name": _("Maternal Last Name"),
            "document_type": _("Document Type"),
            "document_number": _("Document Number"),
            "gender": _("Gender"),
            "birth_date": _("Birth Date"),
            "phone": _("Phone"),
            "email": _("Email"),
            "address": _("Address"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("District"),
            "agency": _("Agency"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required based on model configuration
        self.fields["external_id"].required = True
        self.fields["first_name"].required = True
        self.fields["paternal_last_name"].required = True
        self.fields["document_number"].required = True

        # Set Peru as default country for new applicants
        if not self.instance.pk:
            try:
                peru = Country.objects.get(code2="PE")
                self.fields["country"].initial = peru
            except Country.DoesNotExist:
                pass

        # If the applicant is already approved, disable status field
        if self.instance and self.instance.pk:
            if self.instance.status == choices.ApplicantStatus.APPROVED:
                self.fields["status"].disabled = True
                self.fields["status"].help_text = _(
                    "Status cannot be changed after approval. A partner record has been created."
                )

    def clean_status(self):
        """Validate that status cannot be changed from APPROVED to any other status."""
        status = self.cleaned_data.get("status")

        if self.instance and self.instance.pk:
            old_instance = self.instance.__class__.objects.get(pk=self.instance.pk)

            # Prevent changing from APPROVED to any other status
            if (
                old_instance.status == choices.ApplicantStatus.APPROVED
                and status != choices.ApplicantStatus.APPROVED
            ):
                raise forms.ValidationError(
                    _(
                        "Cannot change status of an approved applicant. "
                        "A partner record has already been created."
                    )
                )

        return status


class PartnerForm(forms.ModelForm):
    """Form for creating and editing Partner instances."""

    class Meta:
        model = models.Partner
        fields = [
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "document_type",
            "document_number",
            "gender",
            "birth_date",
            "phone",
            "email",
            "address",
            "country",
            "region",
            "subregion",
            "city",
            "agency",
            "status",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("First name"),
                }
            ),
            "paternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Paternal last name"),
                }
            ),
            "maternal_last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Maternal last name"),
                }
            ),
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "document_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Document number"),
                }
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "birth_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Phone number"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Email address"),
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Address"),
                }
            ),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select country..."),
                },
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select region..."),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select subregion..."),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select city..."),
                },
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
        }
        labels = {
            "first_name": _("First Name"),
            "paternal_last_name": _("Paternal Last Name"),
            "maternal_last_name": _("Maternal Last Name"),
            "document_type": _("Document Type"),
            "document_number": _("Document Number"),
            "gender": _("Gender"),
            "birth_date": _("Birth Date"),
            "phone": _("Phone"),
            "email": _("Email"),
            "address": _("Address"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("District"),
            "agency": _("Agency"),
            "status": _("Status"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required based on model configuration
        self.fields["first_name"].required = True
        self.fields["paternal_last_name"].required = True
        self.fields["document_number"].required = True

        # Set Peru as default country for new partners
        if not self.instance.pk:
            try:
                peru = Country.objects.get(code2="PE")
                self.fields["country"].initial = peru
            except Country.DoesNotExist:
                pass


class PartnerEmploymentInfoForm(forms.ModelForm):
    """Form for creating and editing Partner Employment Information instances."""

    class Meta:
        model = models.PartnerEmploymentInfo
        fields = [
            "occupation",
            "profession",
            "education_level",
            "employment_type",
            "is_currently_employed",
            "workplace_name",
            "workplace_address",
            "other_workplace",
            "job_position",
            "department",
            "contract_type",
            "contract_start_date",
            "contract_end_date",
            "work_schedule",
            "weekly_hours",
            "base_salary",
            "salary_frequency",
            "additional_income",
            "total_monthly_income",
            "work_phone",
            "work_email",
            "supervisor_name",
            "notes",
        ]
        widgets = {
            "occupation": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Occupation"),
                }
            ),
            "profession": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Profession"),
                }
            ),
            "education_level": forms.Select(attrs={"class": "form-select"}),
            "employment_type": forms.Select(attrs={"class": "form-select"}),
            "is_currently_employed": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "workplace_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Workplace name"),
                }
            ),
            "workplace_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Workplace address"),
                    "rows": 3,
                }
            ),
            "other_workplace": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Other workplace"),
                }
            ),
            "job_position": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Job position"),
                }
            ),
            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Department"),
                }
            ),
            "contract_type": forms.Select(attrs={"class": "form-select"}),
            "contract_start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "contract_end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "work_schedule": forms.Select(attrs={"class": "form-select"}),
            "weekly_hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Weekly hours"),
                    "min": "0",
                    "max": "168",
                }
            ),
            "base_salary": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Base salary (PEN)"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "salary_frequency": forms.Select(attrs={"class": "form-select"}),
            "additional_income": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Additional income (PEN)"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "total_monthly_income": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Total monthly income (PEN)"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "work_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Work phone"),
                }
            ),
            "work_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Work email"),
                }
            ),
            "supervisor_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Supervisor name"),
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Additional notes"),
                    "rows": 4,
                }
            ),
        }
        labels = {
            "occupation": _("Occupation"),
            "profession": _("Profession"),
            "education_level": _("Education Level"),
            "employment_type": _("Employment Type"),
            "is_currently_employed": _("Currently Employed"),
            "workplace_name": _("Workplace Name"),
            "workplace_address": _("Workplace Address"),
            "other_workplace": _("Other Workplace"),
            "job_position": _("Job Position"),
            "department": _("Department"),
            "contract_type": _("Contract Type"),
            "contract_start_date": _("Contract Start Date"),
            "contract_end_date": _("Contract End Date"),
            "work_schedule": _("Work Schedule"),
            "weekly_hours": _("Weekly Hours"),
            "base_salary": _("Base Salary"),
            "salary_frequency": _("Salary Frequency"),
            "additional_income": _("Additional Income"),
            "total_monthly_income": _("Total Monthly Income"),
            "work_phone": _("Work Phone"),
            "work_email": _("Work Email"),
            "supervisor_name": _("Supervisor Name"),
            "notes": _("Notes"),
        }


class ProspectForm(forms.ModelForm):
    """Form for editing Prospect instances."""

    class Meta:
        model = models.Prospect
        fields = [
            "first_name",
            "last_name",
            "document_type",
            "document_number",
            "birth_date",
            "email",
            "phone",
            "status",
            "assigned_to",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("First name"),
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Last name"),
                }
            ),
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "document_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Document number"),
                }
            ),
            "birth_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Email address"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Phone number"),
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Additional notes about the prospect"),
                    "rows": 4,
                }
            ),
        }
        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Names"),
            "document_type": _("Document Type"),
            "document_number": _("Document Number"),
            "birth_date": _("Birth Date"),
            "email": _("Email"),
            "phone": _("Phone"),
            "status": _("Status"),
            "assigned_to": _("Assigned To"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make core fields required
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["document_number"].required = True
        self.fields["email"].required = True

        # Filter assigned_to to only show active employees
        from apps.team import models as team_models

        self.fields["assigned_to"].queryset = team_models.Employee.objects.filter(
            status=team_choices.EmployeeStatus.ACTIVE
        ).select_related("position", "position__area")
