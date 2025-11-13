from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView
from django_filters.views import FilterView

from apps.reports import choices, filtersets, forms, models, tasks


class ReportListView(LoginRequiredMixin, FilterView):
    """
    View to display list of reports with filtering.
    """

    model = models.Report
    filterset_class = filtersets.ReportFilter
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    paginate_by = 5

    def get_queryset(self):
        return models.Report.objects.select_related("report_type").order_by(
            "-created"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Reports"
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    """
    View to display report details.
    """

    model = models.Report
    template_name = "reports/report_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        return models.Report.objects.select_related("report_type")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Report: {self.object.title}"
        return context


class ReportCreateView(LoginRequiredMixin, CreateView):
    """
    View to create new reports.
    """

    model = models.Report
    form_class = forms.ReportCreateForm
    template_name = "reports/report_create.html"
    success_url = reverse_lazy("apps.reports:report-list")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Start async report generation
        tasks.generate_report.delay(self.object.id)

        messages.success(
            self.request,
            f"Report '{self.object.title}' has been queued for generation.",
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Report"
        context["report_types"] = models.ReportType.objects.filter(
            is_active=True
        )
        return context


class ReportDownloadView(LoginRequiredMixin, DetailView):
    """
    View to download generated report file.
    """

    model = models.Report

    def get_queryset(self):
        return models.Report.objects.filter(
            status=choices.ReportStatus.COMPLETED
        )

    def get(self, request, *args, **kwargs):
        report = self.get_object()

        if not report.file_path:
            raise Http404("File not found")

        try:
            with open(report.file_path.path, "rb") as f:
                response = HttpResponse(f.read())

            # Set appropriate headers
            if report.format == choices.ReportFormat.CSV:
                response["Content-Type"] = "text/csv"
                extension = "csv"
            else:  # Excel
                response["Content-Type"] = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                extension = "xlsx"

            filename = f"{report.title}_{report.created.strftime('%Y%m%d_%H%M%S')}.{extension}"
            response["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )

            return response

        except FileNotFoundError:
            raise Http404("File not found")


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """
    View to delete reports.
    """

    model = models.Report
    template_name = "reports/report_delete.html"
    context_object_name = "report"
    success_url = reverse_lazy("apps.reports:report-list")

    def get_queryset(self):
        """Get all reports."""
        return models.Report.objects.all()

    def delete(self, request, *args, **kwargs):
        """Override delete method to add success message and cleanup files."""
        self.object = self.get_object()

        # Delete associated file if exists
        if self.object.file_path:
            try:
                self.object.file_path.delete(save=False)
            except Exception:
                # Continue with deletion even if file cleanup fails
                pass

        response = super().delete(request, *args, **kwargs)

        messages.success(
            self.request,
            f"Report '{self.object.title}' has been deleted successfully.",
        )

        return response

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete Report: {self.object.title}"
        return context
