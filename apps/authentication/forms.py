from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import date

from apps.partners import models as partner_models
from apps.users import models as user_models


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": _("First Name")}),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": _("Last Name")}),
    )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        return user


class ProspectRegistrationForm(forms.ModelForm):
    class Meta:
        model = partner_models.Prospect
        fields = [
            "document_type",
            "document_number",
            "first_name",
            "last_name",
            "birth_date",
            "email",
            "phone",
        ]
        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select form-select-solid",
                    "data-control": "select2",
                }
            ),
            "document_number": forms.TextInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "placeholder": _("Document Number"),
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "placeholder": _("First Name"),
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "placeholder": _("Last Names"),
                }
            ),
            "birth_date": forms.DateInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "type": "date",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "placeholder": _("Email"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control form-control-solid",
                    "placeholder": _("Phone"),
                }
            ),
        }
        labels = {
            "document_type": _("Document Type"),
            "document_number": _("Document Number"),
            "first_name": _("First Name"),
            "last_name": _("Last Names"),
            "birth_date": _("Birth Date"),
            "email": _("Email"),
            "phone": _("Phone"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError(_("You must be at least 18 years old."))
        return birth_date

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            if partner_models.Prospect.objects.filter(email=email).exists():
                raise forms.ValidationError(_("This email is already registered."))
            if user_models.User.objects.filter(email=email).exists():
                raise forms.ValidationError(_("This email is already registered."))
        return email


class DeactivateAccountForm(forms.Form):
    email = forms.EmailField(max_length=254, label=_("Email"), required=True)

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        user = user_models.User.objects.filter(email=email).first()

        if not user:
            raise forms.ValidationError(
                _("The email address is not registered with us.")
            )

        user.is_active = False
        user.save()

        return user
