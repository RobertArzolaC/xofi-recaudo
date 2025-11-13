from constance import config
from dal import autocomplete
from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from apps.campaigns import choices, models


class CampaignForm(forms.ModelForm):
    """Form for creating and editing Campaign instances."""

    class Meta:
        model = models.Campaign
        fields = [
            "name",
            "description",
            "group",
            "execution_date",
            "status",
            "target_amount",
            "average_cost",
            "use_payment_link",
            "channel",
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
            "execution_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
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
            "average_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Average cost"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "use_payment_link": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "channel": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "group": _("Group"),
            "execution_date": _("Execution Date"),
            "status": _("Status"),
            "target_amount": _("Target Amount"),
            "average_cost": _("Average Cost"),
            "use_payment_link": _("Use Payment Link"),
            "channel": _("Channel"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        # Restrict status choices to only DRAFT and SCHEDULED for create/update operations
        self.fields["status"].choices = [
            (
                choices.CampaignStatus.DRAFT,
                choices.CampaignStatus.DRAFT.label,
            ),
            (
                choices.CampaignStatus.SCHEDULED,
                choices.CampaignStatus.SCHEDULED.label,
            ),
        ]

        # Filter channel choices based on ENABLE_TELEGRAM_CHANEL setting
        if not config.ENABLE_TELEGRAM_CHANEL:
            # Exclude Telegram from channel choices
            channel_choices = [
                (value, label)
                for value, label in choices.NotificationChannel.choices
                if value != choices.NotificationChannel.TELEGRAM
            ]
            self.fields["channel"].choices = channel_choices

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


class BulkAddPartnersForm(forms.Form):
    """Form for bulk adding partners to a group via document file."""

    file = forms.FileField(
        label=_("Document File"),
        help_text=_(
            "Upload a text file with document numbers (one per line) or CSV file"
        ),
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".txt,.csv",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super().__init__(*args, **kwargs)

    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get("file")

        if not file:
            raise forms.ValidationError(_("No file was uploaded."))

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                _("File size too large. Maximum size is 5MB.")
            )

        # Check file extension
        file_extension = file.name.split(".")[-1].lower()
        if file_extension not in ["txt", "csv"]:
            raise forms.ValidationError(
                _("Invalid file format. Only .txt and .csv files are allowed.")
            )

        return file

    def process_file(self):
        """Process the file and return list of document numbers and results."""
        from apps.partners.models import Partner

        file = self.cleaned_data["file"]
        file_extension = file.name.split(".")[-1].lower()

        # Read file content
        try:
            content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file.read().decode("latin-1")
            except Exception:
                raise forms.ValidationError(
                    _(
                        "Unable to read file. Please ensure it's a valid text file."
                    )
                )

        # Extract document numbers from file
        documents = []
        if file_extension == "csv":
            import csv
            import io

            reader = csv.reader(io.StringIO(content))
            for row in reader:
                if row and row[0].strip():
                    documents.append(row[0].strip())
        else:  # txt file
            for line in content.splitlines():
                line = line.strip()
                if line:
                    documents.append(line)

        # Remove duplicates while preserving order
        seen = set()
        unique_documents = []
        for document in documents:
            if document not in seen:
                seen.add(document)
                unique_documents.append(document)

        # Process document numbers and find partners
        results = {
            "total_documents": len(unique_documents),
            "found": [],
            "not_found": [],
            "already_in_group": [],
            "added": [],
        }

        if not self.group:
            return results

        existing_partner_ids = set(
            self.group.partners.values_list("document_number", flat=True)
        )

        for document in unique_documents:
            try:
                partner = Partner.objects.get(document_number=document)
                results["found"].append(
                    {
                        "document": document,
                        "partner": partner,
                    }
                )

                if document in existing_partner_ids:
                    results["already_in_group"].append(document)
                else:
                    self.group.partners.add(partner)
                    results["added"].append(
                        {
                            "document": document,
                            "partner": partner,
                        }
                    )
            except Partner.DoesNotExist:
                results["not_found"].append(document)
            except Partner.MultipleObjectsReturned:
                results["not_found"].append(document)

        return results


class CampaignCSVFileForm(forms.ModelForm):
    """Form for creating and editing CSV/Excel file-based campaigns."""

    class Meta:
        model = models.CampaignCSVFile
        fields = [
            "name",
            "description",
            "file",
            "execution_date",
            "status",
            "channel",
            "use_payment_link",
            "target_amount",
            "average_cost",
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
            "file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".csv,.xlsx,.xls",
                }
            ),
            "execution_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "channel": forms.Select(
                attrs={"class": "form-select", "data-control": "select2"}
            ),
            "use_payment_link": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "target_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Target amount"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "average_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Average cost"),
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "file": _("CSV/Excel File"),
            "execution_date": _("Execution Date"),
            "status": _("Status"),
            "channel": _("Channel"),
            "use_payment_link": _("Use Payment Link"),
            "target_amount": _("Target Amount"),
            "average_cost": _("Average Cost"),
        }
        help_texts = {
            "file": _(
                "Upload a CSV or Excel file with contact information. "
                "Required columns: full_name, amount. "
                "Optional columns: email, phone, document_number."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["file"].required = not self.instance.pk

        # Restrict status choices to only DRAFT and SCHEDULED
        self.fields["status"].choices = [
            (
                choices.CampaignStatus.DRAFT,
                choices.CampaignStatus.DRAFT.label,
            ),
            (
                choices.CampaignStatus.SCHEDULED,
                choices.CampaignStatus.SCHEDULED.label,
            ),
        ]

        # Filter channel choices based on ENABLE_TELEGRAM_CHANEL setting
        if not config.ENABLE_TELEGRAM_CHANEL:
            # Exclude Telegram from channel choices
            channel_choices = [
                (value, label)
                for value, label in choices.NotificationChannel.choices
                if value != choices.NotificationChannel.TELEGRAM
            ]
            self.fields["channel"].choices = channel_choices

        # Add file validator
        self.fields["file"].validators.append(
            FileExtensionValidator(
                allowed_extensions=["csv", "xlsx", "xls"],
                message=_("Only CSV and Excel files are allowed."),
            )
        )

    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get("file")

        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    _("File size too large. Maximum size is 10MB.")
                )

            # Check file extension
            file_extension = file.name.split(".")[-1].lower()
            if file_extension not in ["csv", "xlsx", "xls"]:
                raise forms.ValidationError(
                    _(
                        "Invalid file format. Only CSV and Excel files are allowed."
                    )
                )

        return file

    def save(self, commit=True):
        """Save the form and trigger validation if file is new."""
        instance = super().save(commit=False)

        # Set campaign type
        instance.campaign_type = choices.CampaignType.FILE

        if commit:
            instance.save()

            # If a new file was uploaded, trigger validation
            if "file" in self.changed_data and instance.file:
                # Import here to avoid circular imports
                from apps.campaigns import tasks

                # Queue validation task
                tasks.validate_csv_campaign.delay(instance.id)

        return instance
