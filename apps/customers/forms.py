from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from constance import config
from dal import autocomplete
from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.customers import mixins, models
from apps.users import models as user_models


class AccountCreationForm(mixins.PermissionFormMixin, SignupForm):
    first_name = forms.CharField(max_length=30, label="First name")
    last_name = forms.CharField(max_length=30, label="Last name")
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password1", None)
        self.fields.pop("password2", None)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        if user_models.User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists")
            )

        return cleaned_data

    def save(self, request):
        with transaction.atomic():
            user = super(AccountCreationForm, self).save(request)

            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.user_type = self.cleaned_data["user_type"]
            user.avatar = self.cleaned_data["avatar"]
            user.must_change_password = True

            temp_password = user_models.User.objects.make_random_password()
            user.set_password(temp_password)
            user.save()
            self.save_permissions(user)

            EmailAddress.objects.get_or_create(
                user=user, email=user.email, primary=True, verified=False
            )

            if config.ENABLE_SEND_EMAIL:
                send_email_confirmation(request, user, signup=True)

            return user


class AccountUpdateForm(mixins.PermissionFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(max_length=30, label=_("Last name"))
    email = forms.EmailField(max_length=254, label=_("Email"), disabled=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = models.Account
        fields = ["avatar"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            self.fields["avatar"].initial = self.instance.user.avatar

    def save(self, commit=True):
        account = super().save(commit=False)
        user = account.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.avatar = self.cleaned_data.get("avatar")

        user.save()
        account.save()
        self.save_permissions(user)

        return account


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = "__all__"


class CompanyForm(forms.ModelForm):
    """Form for creating and editing Company instances."""

    class Meta:
        model = models.Company
        fields = [
            "logo",
            "tax_id",
            "name",
            "phone",
            "email",
            "domain",
            "address",
            "country",
            "region",
            "subregion",
            "city",
        ]
        widgets = {
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "tax_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tax ID (11 digits)"),
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Company name"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Contact phone"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Contact email"),
                }
            ),
            "domain": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Web domain (optional)"),
                }
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Address")}
            ),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={"class": "form-select", "data-control": "select2"},
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Department"),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Province"),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("District"),
                },
            ),
        }
        labels = {
            "logo": _("Logo"),
            "tax_id": _("Tax ID"),
            "name": _("Name"),
            "phone": _("Contact Phone"),
            "email": _("Contact Email"),
            "domain": _("Domain"),
            "address": _("Address"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("District"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required based on model configuration
        self.fields["tax_id"].required = True
        self.fields["name"].required = True
        self.fields["email"].required = True

    def save(self, commit: bool = True):
        """Save form and update Constance values."""
        instance = super().save(commit)

        # Update Constance values with Company model fields
        config.PROJECT_NAME = self.cleaned_data["name"]

        # Handle logo field properly - use the saved instance's logo field
        if self.cleaned_data["logo"]:
            config.COMPANY_LOGO_WHITE = instance.logo.url

        if self.cleaned_data["domain"]:
            config.COMPANY_DOMAIN = self.cleaned_data["domain"]

        if self.cleaned_data["phone"]:
            config.COMPANY_PHONE = self.cleaned_data["phone"]

        return instance


class AgencyForm(forms.ModelForm):
    """Form for creating and editing Agency instances."""

    class Meta:
        model = models.Agency
        fields = [
            "name",
            "description",
            "code",
            "is_active",
            "phone",
            "email",
            "address",
            "country",
            "region",
            "subregion",
            "city",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Agency name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Agency description"),
                    "rows": 3,
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Unique agency code"),
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Contact phone"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Contact email"),
                }
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Address")}
            ),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={"class": "form-select", "data-control": "select2"},
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Department"),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Province"),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("District"),
                },
            ),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "code": _("Code"),
            "is_active": _("Active"),
            "phone": _("Contact Phone"),
            "email": _("Contact Email"),
            "address": _("Address"),
            "country": _("Country"),
            "region": _("Department"),
            "subregion": _("Province"),
            "city": _("District"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required based on model configuration
        self.fields["name"].required = True
        self.fields["code"].required = True
