import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, List

import openpyxl

from apps.campaigns import choices

logger = logging.getLogger(__name__)


class CSVValidationService:
    """Service for validating CSV/Excel files for campaigns."""

    REQUIRED_COLUMNS = ["full_name", "amount"]
    OPTIONAL_COLUMNS = ["email", "phone", "telegram_id", "document_number"]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    @classmethod
    def validate_campaign_csv(cls, campaign_csv):
        """
        Validate the uploaded CSV file.

        Args:
            campaign_csv: CampaignCSVFile instance

        Returns:
            dict: Validation results
        """
        from apps.campaigns.models import CSVContact

        logger.info(f"Starting CSV validation for campaign {campaign_csv.id}")

        # Update status to processing
        campaign_csv.validation_status = choices.ValidationStatus.PROCESSING
        campaign_csv.save(update_fields=["validation_status"])

        try:
            # Parse the file
            file_extension = campaign_csv.file.name.split(".")[-1].lower()
            if file_extension == "csv":
                rows = cls._parse_csv_file(campaign_csv.file)
            elif file_extension in ["xlsx", "xls"]:
                rows = cls._parse_excel_file(campaign_csv.file)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

            logger.info(f"Parsed {len(rows)} rows from file")

            # Validate rows and create contacts
            validation_results = {
                "total_contacts": len(rows),
                "valid_contacts": 0,
                "invalid_contacts": 0,
                "errors": [],
            }

            # Delete existing contacts for this campaign
            CSVContact.objects.filter(campaign=campaign_csv).delete()

            contacts_to_create = []

            for row_number, row_data in enumerate(
                rows, start=2
            ):  # Start from 2 (header is row 1)
                validation_result = cls._validate_row(row_data, row_number)

                # Create CSVContact instance
                contact = CSVContact(
                    campaign=campaign_csv,
                    full_name=row_data.get("full_name", ""),
                    email=row_data.get("email"),
                    phone=row_data.get("phone"),
                    telegram_id=row_data.get("telegram_id"),
                    document_number=row_data.get("document_number"),
                    amount=validation_result.get("amount", Decimal("0")),
                    additional_data=row_data.get("additional_data", {}),
                    is_valid=validation_result["is_valid"],
                    validation_errors=validation_result.get("errors", []),
                    row_number=row_number,
                )

                contacts_to_create.append(contact)

                if validation_result["is_valid"]:
                    validation_results["valid_contacts"] += 1
                else:
                    validation_results["invalid_contacts"] += 1
                    validation_results["errors"].extend(
                        [
                            f"Row {row_number}: {err}"
                            for err in validation_result.get("errors", [])
                        ]
                    )

            # Bulk create contacts
            if contacts_to_create:
                CSVContact.objects.bulk_create(contacts_to_create)
                logger.info(f"Created {len(contacts_to_create)} CSV contacts")

            # Update campaign with validation results
            campaign_csv.total_contacts = validation_results["total_contacts"]
            campaign_csv.valid_contacts = validation_results["valid_contacts"]
            campaign_csv.invalid_contacts = validation_results[
                "invalid_contacts"
            ]
            campaign_csv.validation_result = validation_results

            # Determine final validation status
            if validation_results["valid_contacts"] == 0:
                campaign_csv.validation_status = choices.ValidationStatus.FAILED
            elif validation_results["invalid_contacts"] > 0:
                campaign_csv.validation_status = (
                    choices.ValidationStatus.PARTIAL
                )
            else:
                campaign_csv.validation_status = (
                    choices.ValidationStatus.VALIDATED
                )

            campaign_csv.save(
                update_fields=[
                    "total_contacts",
                    "valid_contacts",
                    "invalid_contacts",
                    "validation_result",
                    "validation_status",
                ]
            )

            logger.info(
                f"CSV validation completed for campaign {campaign_csv.id}: "
                f"{validation_results['valid_contacts']} valid, "
                f"{validation_results['invalid_contacts']} invalid"
            )

            return validation_results

        except Exception as e:
            logger.exception(
                f"Error validating CSV for campaign {campaign_csv.id}: {e}"
            )

            # Update campaign with error status
            campaign_csv.validation_status = choices.ValidationStatus.FAILED
            campaign_csv.validation_result = {"error": str(e)}
            campaign_csv.save(
                update_fields=["validation_status", "validation_result"]
            )

            raise

    @classmethod
    def _parse_csv_file(cls, file) -> List[Dict]:
        """Parse CSV file and return list of row dictionaries."""
        file.seek(0)
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        rows = []
        for row in reader:
            # Normalize keys to lowercase
            normalized_row = {
                k.lower().strip(): v.strip() if v else None
                for k, v in row.items()
            }
            rows.append(normalized_row)

        return rows

    @classmethod
    def _parse_excel_file(cls, file) -> List[Dict]:
        """Parse Excel file and return list of row dictionaries."""
        file.seek(0)
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active

        # Get headers from first row
        headers = [
            cell.value.lower().strip() if cell.value else f"column_{idx}"
            for idx, cell in enumerate(sheet[1], start=1)
        ]

        rows = []
        for row_idx, row in enumerate(
            sheet.iter_rows(min_row=2, values_only=True), start=2
        ):
            row_dict = {}
            for header, value in zip(headers, row):
                row_dict[header] = (
                    str(value).strip() if value is not None else None
                )
            rows.append(row_dict)

        return rows

    @classmethod
    def _validate_row(cls, row_data: Dict, row_number: int) -> Dict:
        """
        Validate a single row of data.

        Args:
            row_data: Dictionary with row data
            row_number: Row number in file

        Returns:
            dict: Validation result with is_valid, amount, and errors
        """
        errors = []
        is_valid = True

        # Check required fields
        full_name = row_data.get("full_name")
        if not full_name:
            errors.append("Missing required field: full_name")
            is_valid = False

        # Validate amount
        amount_str = row_data.get("amount")
        amount = Decimal("0")

        if not amount_str:
            errors.append("Missing required field: amount")
            is_valid = False
        else:
            try:
                amount = Decimal(str(amount_str).replace(",", ""))
                if amount <= 0:
                    errors.append(
                        f"Invalid amount: {amount_str} (must be greater than 0)"
                    )
                    is_valid = False
            except (InvalidOperation, ValueError):
                errors.append(f"Invalid amount format: {amount_str}")
                is_valid = False

        # Validate email if provided
        email = row_data.get("email")
        if email and "@" not in email:
            errors.append(f"Invalid email format: {email}")
            # Don't mark as invalid, just warning

        # Validate phone if provided
        phone = row_data.get("phone")
        if phone:
            clean_phone = "".join(filter(str.isdigit, phone))
            if len(clean_phone) < 9:
                errors.append(f"Invalid phone format: {phone} (too short)")
                # Don't mark as invalid, just warning

        # Validate telegram_id if provided
        telegram_id = row_data.get("telegram_id")
        if telegram_id:
            # Telegram usernames start with @ and IDs are numeric
            telegram_str = str(telegram_id).strip()
            if not telegram_str:
                errors.append("Telegram ID cannot be empty if provided")
            elif not (telegram_str.startswith("@") or telegram_str.isdigit()):
                errors.append(
                    f"Invalid telegram_id format: {telegram_id} "
                    "(must start with @ for username or be numeric for ID)"
                )
                # Don't mark as invalid, just warning

        return {
            "is_valid": is_valid,
            "amount": amount,
            "errors": errors,
        }


class CSVCampaignNotificationService:
    """Service for creating notifications from CSV campaigns."""

    @classmethod
    def create_notifications_from_csv(cls, campaign_csv):
        """
        Create notifications for all valid contacts in the CSV.

        This is now handled by the FileCampaignExecutor in the notifications app.
        This method is kept for backward compatibility.

        Args:
            campaign_csv: CampaignCSVFile instance

        Returns:
            dict: Summary of created notifications
        """
        from apps.notifications.services import NotificationService

        return NotificationService.execute_campaign(campaign_csv)
