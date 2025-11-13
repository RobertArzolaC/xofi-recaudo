from django import forms
from django.utils.translation import gettext_lazy as _

from apps.reports import choices
from apps.reports.models import Report, ReportType


class ReportCreateForm(forms.ModelForm):
    """
    Form to create new reports with dynamic filters.
    """

    class Meta:
        model = Report
        fields = ["title", "description", "report_type", "format", "filters"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Enter report title")}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Enter report description (optional)"),
                }
            ),
            "report_type": forms.Select(
                attrs={"class": "form-select", "id": "id_report_type"}
            ),
            "format": forms.Select(attrs={"class": "form-select"}),
            "filters": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter active report types
        self.fields["report_type"].queryset = ReportType.objects.filter(is_active=True)

        # Set format choices
        self.fields["format"].choices = choices.ReportFormat.choices

        # Make fields required
        self.fields["title"].required = True
        self.fields["report_type"].required = True
        self.fields["format"].required = True

    def clean_filters(self):
        """
        Validate and clean the filters JSON data.
        """
        filters = self.cleaned_data.get("filters", "{}")

        if isinstance(filters, str):
            try:
                import json

                filters = json.loads(filters)
            except (json.JSONDecodeError, TypeError):
                filters = {}

        return filters

    def clean(self):
        """
        Perform additional validation.
        """
        cleaned_data = super().clean()
        report_type = cleaned_data.get("report_type")
        filters = cleaned_data.get("filters", {})

        if report_type:
            # Validate required filters
            required_filters = report_type.filters.filter(
                is_required=True, is_active=True
            )

            for required_filter in required_filters:
                filter_value = filters.get(required_filter.name)

                if not filter_value:
                    self.add_error(
                        "filters", _(f'Filter "{required_filter.label}" is required')
                    )

        return cleaned_data


class ReportFilterForm(forms.Form):
    """
    Dynamic form for report filters.
    This form is generated dynamically based on the selected report type.
    """

    def __init__(self, report_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if report_type:
            self._add_filter_fields(report_type)

    def _add_filter_fields(self, report_type):
        """
        Add filter fields based on the report type configuration.
        """
        filters = report_type.filters.filter(is_active=True).order_by("order", "name")

        for filter_obj in filters:
            field_name = filter_obj.name
            field_kwargs = {
                "label": filter_obj.label,
                "required": filter_obj.is_required,
                "help_text": filter_obj.options.get("help_text", ""),
            }

            # Create field based on filter type
            if filter_obj.filter_type == choices.FilterType.DATE:
                field = forms.DateField(
                    widget=forms.DateInput(
                        attrs={"type": "date", "class": "form-control"}
                    ),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.DATETIME:
                field = forms.DateTimeField(
                    widget=forms.DateTimeInput(
                        attrs={"type": "datetime-local", "class": "form-control"}
                    ),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.TEXT:
                field = forms.CharField(
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": filter_obj.options.get("placeholder", ""),
                        }
                    ),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.NUMBER:
                field = forms.IntegerField(
                    widget=forms.NumberInput(
                        attrs={
                            "class": "form-control",
                            "min": filter_obj.options.get("min", ""),
                            "max": filter_obj.options.get("max", ""),
                        }
                    ),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.SELECT:
                choices_list = filter_obj.options.get("choices", [])
                field = forms.ChoiceField(
                    choices=[("", "--- Select ---")] + choices_list,
                    widget=forms.Select(attrs={"class": "form-select"}),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.MULTISELECT:
                choices_list = filter_obj.options.get("choices", [])
                field = forms.MultipleChoiceField(
                    choices=choices_list,
                    widget=forms.CheckboxSelectMultiple(
                        attrs={"class": "form-check-input"}
                    ),
                    **field_kwargs,
                )

            elif filter_obj.filter_type == choices.FilterType.BOOLEAN:
                field = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                    **field_kwargs,
                )

            else:
                # Default to text field
                field = forms.CharField(
                    widget=forms.TextInput(attrs={"class": "form-control"}),
                    **field_kwargs,
                )

            self.fields[field_name] = field
