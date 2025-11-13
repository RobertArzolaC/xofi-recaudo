from django.urls import path

from apps.reports import api, views

app_name = "apps.reports"

urlpatterns = [
    # Main views
    path("", views.ReportListView.as_view(), name="report-list"),
    path("create/", views.ReportCreateView.as_view(), name="report-create"),
    path("<int:pk>/", views.ReportDetailView.as_view(), name="report-detail"),
    path(
        "<int:pk>/download/", views.ReportDownloadView.as_view(), name="report-download"
    ),
    path("<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report-delete"),
    # API endpoints
    path(
        "api/<int:pk>/status/",
        api.ReportStatusAPIView.as_view(),
        name="api-report-status",
    ),
    path(
        "api/report-types/<int:report_type_id>/filters/",
        api.ReportFiltersAPIView.as_view(),
        name="api-report-filters",
    ),
]
