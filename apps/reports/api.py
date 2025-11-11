from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.models import Report, ReportType


@extend_schema(exclude=True)
class ReportStatusAPIView(APIView):
    """
    API view to get report status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report = Report.objects.select_related("report_type").get(pk=pk)

            data = {
                "id": report.id,
                "title": report.title,
                "status": report.status,
                "status_display": report.get_status_display(),
                "is_processing": report.is_processing,
                "is_completed": report.is_completed,
                "is_failed": report.is_failed,
                "progress": 100
                if report.is_completed
                else (50 if report.status == "processing" else 0),
                "created_at": report.created.isoformat(),
                "started_at": report.started_at.isoformat()
                if report.started_at
                else None,
                "completed_at": report.completed_at.isoformat()
                if report.completed_at
                else None,
                "duration": report.duration,
                "record_count": report.record_count,
                "file_size": report.file_size,
                "error_message": report.error_message,
                "download_url": f"/reports/{report.id}/download/"
                if report.file_path
                else None,
            }

            return Response(data, status=status.HTTP_200_OK)

        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(exclude=True)
class ReportFiltersAPIView(APIView):
    """
    API view to get available filters for a report type.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, report_type_id):
        try:
            report_type = ReportType.objects.get(pk=report_type_id, is_active=True)
            filters = report_type.filters.filter(is_active=True).order_by(
                "order", "name"
            )

            filter_data = []
            for filter_obj in filters:
                filter_data.append(
                    {
                        "name": filter_obj.name,
                        "label": filter_obj.label,
                        "field_name": filter_obj.field_name,
                        "filter_type": filter_obj.filter_type,
                        "options": filter_obj.options,
                        "is_required": filter_obj.is_required,
                        "order": filter_obj.order,
                    }
                )

            return Response(
                {
                    "filters": filter_data,
                    "report_type": {
                        "id": report_type.id,
                        "name": report_type.name,
                        "code": report_type.code,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ReportType.DoesNotExist:
            return Response(
                {"error": "Report type not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
