import logging
import os
from typing import Any, Dict

from celery import shared_task
from django.utils import timezone

from apps.reports import choices
from apps.reports.generators.factory import ReportGeneratorFactory
from apps.reports.models import Report

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_report(self, report_id: int) -> Dict[str, Any]:
    """
    Celery task to generate a report asynchronously.
    """
    try:
        report = Report.objects.get(id=report_id)
        report.status = choices.ReportStatus.PROCESSING
        report.started_at = timezone.now()
        report.celery_task_id = self.request.id
        report.save()

        # Create report generator
        generator = ReportGeneratorFactory.create_generator(
            report.report_type.code, report.filters
        )

        # Generate report file
        file_content = generator.generate(report.format)

        # Save file
        report.file_path.save(file_content.name, file_content, save=False)

        # Update report status
        report.status = choices.ReportStatus.COMPLETED
        report.completed_at = timezone.now()
        report.record_count = generator.get_record_count()

        # Get file size
        if report.file_path and os.path.exists(report.file_path.path):
            report.file_size = os.path.getsize(report.file_path.path)

        report.save()

        logger.info(f"Report {report_id} generated successfully")

        return {
            "status": "completed",
            "report_id": report_id,
            "file_path": report.file_path.url if report.file_path else None,
            "record_count": report.record_count,
            "file_size": report.file_size,
        }

    except Report.DoesNotExist:
        logger.error(f"Report with id {report_id} does not exist")
        return {
            "status": "failed",
            "error": f"Report with id {report_id} does not exist",
        }

    except Exception as exc:
        logger.error(f"Error generating report {report_id}: {str(exc)}")

        try:
            report = Report.objects.get(id=report_id)
            report.status = choices.ReportStatus.FAILED
            report.error_message = str(exc)
            report.completed_at = timezone.now()
            report.save()
        except Report.DoesNotExist:
            pass

        return {"status": "failed", "report_id": report_id, "error": str(exc)}


@shared_task
def cleanup_old_reports(days: int = 30) -> Dict[str, Any]:
    """
    Celery task to cleanup old report files.
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    old_reports = Report.objects.filter(
        created__lt=cutoff_date, status=choices.ReportStatus.COMPLETED
    )

    deleted_count = 0
    for report in old_reports:
        if report.file_path and os.path.exists(report.file_path.path):
            try:
                os.remove(report.file_path.path)
                report.file_path = None
                report.save()
                deleted_count += 1
            except Exception as exc:
                logger.error(f"Error deleting file for report {report.id}: {str(exc)}")

    logger.info(f"Cleaned up {deleted_count} old report files")

    return {"status": "completed", "deleted_count": deleted_count}
