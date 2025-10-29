from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.campaigns import models


class CampaignForm(forms.ModelForm):
    """Form for creating and editing Campaign instances."""

    class Meta:
        model = models.Campaign
        fields = [
            "name",
            "description",
            "group",
            "start_date",
            "end_date",
            "status",
            "target_amount",
            "execution_time",
            "notify_3_days_before",
            "notify_on_due_date",
            "notify_3_days_after",
            "notify_7_days_after",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Campaign name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Campaign description"),
                    "rows": 4,
                }
            ),
            "group": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "target_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Target amount"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "execution_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "notify_3_days_before": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notify_on_due_date": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notify_3_days_after": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notify_7_days_after": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "group": _("Group"),
            "start_date": _("Start Date"),
            "end_date": _("End Date"),
            "status": _("Status"),
            "target_amount": _("Target Amount"),
            "execution_time": _("Execution Time"),
            "notify_3_days_before": _("Notify 3 Days Before"),
            "notify_on_due_date": _("Notify on Due Date"),
            "notify_3_days_after": _("Notify 3 Days After"),
            "notify_7_days_after": _("Notify 7 Days After"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        # If we have an instance with a group, set the target_amount to the group's total debt
        if self.instance and self.instance.pk and self.instance.group:
            if not self.instance.target_amount:
                self.initial["target_amount"] = (
                    self.instance.group.total_outstanding_debt
                )

        # Add data attributes for JavaScript functionality
        self.fields["group"].widget.attrs.update(
            {
                "data-debt-url-base": "/campaigns/ajax/group-debt/",
                "onchange": "updateTargetAmount(this.value)",
            }
        )

        self.fields["target_amount"].widget.attrs.update(
            {
                "id": "id_target_amount",
                "readonly": True,  # Make field read-only
            }
        )

    def clean_target_amount(self):
        """Validate and potentially auto-set target_amount based on selected group."""
        target_amount = self.cleaned_data.get("target_amount")
        group = self.cleaned_data.get("group")

        # If no target_amount is provided but we have a group, use the group's debt
        if not target_amount and group:
            target_amount = group.total_outstanding_debt

        return target_amount


class GroupForm(forms.ModelForm):
    """Form for creating and editing Group instances."""

    class Meta:
        model = models.Group
        fields = [
            "name",
            "description",
            "partners",
            "priority",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Group name"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Group description"),
                    "rows": 4,
                }
            ),
            "partners": autocomplete.ModelSelect2Multiple(
                url="apps.partners:partner-autocomplete",
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "data-allow-clear": "true",
                    "data-placeholder": _("Select partners..."),
                },
            ),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "partners": _("Partners"),
            "priority": _("Priority"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
