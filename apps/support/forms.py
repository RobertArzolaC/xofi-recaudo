from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.support import models
from apps.team import choices as team_choices
from apps.team import models as team_models


class TicketForm(forms.ModelForm):
    """Form for creating and editing Ticket instances."""

    class Meta:
        model = models.Ticket
        fields = [
            "partner",
            "subject",
            "description",
            "priority",
            "status",
            "assigned_to",
        ]
        widgets = {
            "partner": autocomplete.ModelSelect2(
                url="apps.partners:partner-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-placeholder": _("Select partner..."),
                },
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Brief description of the issue"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Detailed description of the issue"),
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Auto-assign or select employee..."),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make assigned_to optional (auto-assignment will handle it)
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].empty_label = _("Auto-assign")

        # Filter employees to only show active ones
        self.fields[
            "assigned_to"
        ].queryset = team_models.Employee.objects.filter(
            status=team_choices.EmployeeStatus.ACTIVE
        ).select_related("position")


class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to tickets."""

    class Meta:
        model = models.TicketComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Add your comment here..."),
                }
            ),
        }


class TicketStatusUpdateForm(forms.ModelForm):
    """Simplified form for updating ticket status."""

    class Meta:
        model = models.Ticket
        fields = ["status", "assigned_to"]
        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "assigned_to"
        ].queryset = team_models.Employee.objects.filter(
            status=team_choices.EmployeeStatus.ACTIVE
        ).select_related("position")
        self.fields["assigned_to"].required = False


class TicketWhatsAppResponseForm(forms.Form):
    """Form for sending a WhatsApp response to the partner."""

    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Write your WhatsApp response here..."),
                "id": "whatsapp_response_message",
            }
        ),
        label=_("Response Message"),
        max_length=4096,
        help_text=_(
            "This message will be sent via WhatsApp to the partner's phone number."
        ),
    )
