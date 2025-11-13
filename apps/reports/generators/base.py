"""
Base report generator using Strategy pattern.

This module provides the abstract base class that all report generators must inherit from.
"""

import csv
import io
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from django.core.files.base import ContentFile
from django.db.models import QuerySet

try:
    import pandas as pd
except ImportError:
    pd = None


class BaseReportGenerator(ABC):
    """
    Abstract base class for report generators using Strategy pattern.

    All report generators must implement:
    - get_queryset(): Returns filtered data
    - get_headers(): Returns column headers
    - get_data(): Transforms queryset into report rows
    """

    def __init__(self, report_type: str, filters: Dict[str, Any]):
        """
        Initialize report generator.

        Args:
            report_type: Code identifying the report type
            filters: Dictionary with filter parameters
        """
        self.report_type = report_type
        self.filters = filters

    @abstractmethod
    def get_queryset(self) -> QuerySet:
        """
        Get the filtered queryset for the report.

        Must be implemented by subclasses.

        Returns:
            QuerySet with filtered data
        """
        pass

    @abstractmethod
    def get_headers(self) -> List[str]:
        """
        Get column headers for the report.

        Must be implemented by subclasses.

        Returns:
            List of column header strings
        """
        pass

    @abstractmethod
    def get_data(self, queryset: QuerySet) -> List[List[Any]]:
        """
        Transform queryset into report data rows.

        Must be implemented by subclasses.

        Args:
            queryset: Filtered queryset from get_queryset()

        Returns:
            List of rows, where each row is a list of values
        """
        pass

    def generate(self, format_type: str = "csv") -> ContentFile:
        """
        Generate report in specified format.

        This is the main public method that orchestrates report generation.

        Args:
            format_type: 'csv' or 'excel'

        Returns:
            ContentFile with generated report

        Raises:
            ValueError: If format_type is not supported
        """
        # Get data
        queryset = self.get_queryset()
        headers = self.get_headers()
        data = self.get_data(queryset)

        # Generate based on format
        if format_type == "csv":
            return self._generate_csv(headers, data)
        elif format_type == "excel":
            return self._generate_excel(headers, data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _generate_csv(self, headers: List[str], data: List[List[Any]]) -> ContentFile:
        """
        Generate CSV format report.

        Args:
            headers: Column headers
            data: Report data rows

        Returns:
            ContentFile with CSV data
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(headers)

        # Write data
        writer.writerows(data)

        # Create file
        content = output.getvalue()
        output.close()

        return ContentFile(content.encode("utf-8"), name=f"{self.report_type}.csv")

    def _generate_excel(
        self, headers: List[str], data: List[List[Any]]
    ) -> ContentFile:
        """
        Generate Excel format report using pandas.

        Args:
            headers: Column headers
            data: Report data rows

        Returns:
            ContentFile with Excel data

        Raises:
            ImportError: If pandas is not installed
        """
        if pd is None:
            raise ImportError(
                "pandas is required for Excel export. Install with: pip install pandas openpyxl"
            )

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")

        # Create file
        content = output.getvalue()
        output.close()

        return ContentFile(content, name=f"{self.report_type}.xlsx")

    def get_record_count(self) -> int:
        """
        Get the number of records in the report.

        Returns:
            Record count
        """
        queryset = self.get_queryset()
        return queryset.count()
