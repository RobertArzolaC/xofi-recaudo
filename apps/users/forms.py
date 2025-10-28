from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _

from apps.users import models as user_models
from apps.users.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


class UserSettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(
        max_length=30, label=_("Last name"), required=False
    )

    class Meta:
        model = user_models.User
        fields = ["first_name", "last_name"]


class UserCreateForm(forms.ModelForm):
    """Form for creating new users with role assignment."""

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter password"),
            }
        ),
    )
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm password"),
            }
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Roles"),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active", "groups"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Email address"),
                }
            ),
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
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "email": _("Email"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "is_active": _("Active"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["first_name"].required = True

    def clean_password2(self):
        """Validate that both passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords do not match"))
        return password2

    def save(self, commit: bool = True):
        """Save user with hashed password and assigned roles."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()  # Save many-to-many relationships (groups)
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users."""

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Roles"),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active", "groups"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Email address"),
                }
            ),
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
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "email": _("Email"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "is_active": _("Active"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        # Pre-select current groups if editing
        if self.instance and self.instance.pk:
            self.fields["groups"].initial = self.instance.groups.all()


class UserRolesForm(forms.ModelForm):
    """Form for managing roles assigned to a user."""

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Roles"),
    )

    class Meta:
        model = User
        fields = ["groups"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select current groups if editing
        if self.instance and self.instance.pk:
            self.fields["groups"].initial = self.instance.groups.all()


class UserPermissionsForm(forms.ModelForm):
    """Form for managing direct permissions assigned to a user."""

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "content_type__model", "codename"
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Permissions"),
    )

    class Meta:
        model = User
        fields = ["user_permissions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select current permissions if editing
        if self.instance and self.instance.pk:
            self.fields[
                "user_permissions"
            ].initial = self.instance.user_permissions.all()
