import logging
import re
from datetime import date, datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ReceiptDataExtractionService:
    """Service for extracting payment data from receipt captions and images."""

    def __init__(self):
        """Initialize the extraction service."""
        self.default_amount = 0.01  # Placeholder amount
        self.default_date = date.today().strftime("%Y-%m-%d")

    def extract_from_caption(
        self, caption: str
    ) -> Dict[str, Optional[float | str]]:
        """
        Extract payment information from user caption.

        Args:
            caption: User-provided caption text

        Returns:
            Dict with extracted amount and date, or None if not found
        """
        if not caption:
            return {"amount": None, "date": None}

        logger.info(f"Extracting data from caption: {caption}")

        amount = self._extract_amount_from_caption(caption)
        payment_date = self._extract_date_from_caption(caption)

        return {"amount": amount, "date": payment_date}

    def _extract_amount_from_caption(self, caption: str) -> Optional[float]:
        """
        Extract amount from caption using regex patterns.

        Args:
            caption: User caption text

        Returns:
            Extracted amount as float or None if not found
        """
        try:
            # Patterns for amount extraction (supports various formats)
            amount_patterns = [
                r"(?:monto|pago|importe|cantidad)\s*:?\s*(\d+[.,]?\d*)",
                r"(\d+[.,]\d{1,2})\s*(?:soles?|nuevos soles|s/)",
                r"s/\s*(\d+[.,]\d{1,2})",
                r"total\s*:?\s*(\d+[.,]\d{1,2})",
                r"(\d+[.,]\d{1,2})",  # Generic number pattern (last resort)
            ]

            for pattern in amount_patterns:
                match = re.search(pattern, caption.lower())
                if match:
                    amount_str = match.group(1).replace(",", ".")
                    try:
                        amount = float(amount_str)
                        # Validate reasonable amount range
                        if 0.01 <= amount <= 999999.99:
                            logger.info(
                                f"Extracted amount from caption: {amount}"
                            )
                            return amount
                    except ValueError:
                        continue

            logger.warning("No valid amount found in caption")
            return None

        except Exception as e:
            logger.error(f"Error extracting amount from caption: {e}")
            return None

    def _extract_date_from_caption(self, caption: str) -> Optional[str]:
        """
        Extract date from caption using regex patterns.

        Args:
            caption: User caption text

        Returns:
            Extracted date in YYYY-MM-DD format or None if not found
        """
        try:
            # Patterns for date extraction
            date_patterns = [
                r"(?:fecha|date)\s*:?\s*(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
                r"(?:fecha|date)\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{4})",  # DD/MM/YYYY or DD-MM-YYYY
                r"(\d{4}-\d{2}-\d{2})",  # Just YYYY-MM-DD
                r"(\d{2}[/-]\d{2}[/-]\d{4})",  # Just DD/MM/YYYY or DD-MM-YYYY
            ]

            for pattern in date_patterns:
                match = re.search(pattern, caption.lower())
                if match:
                    date_str = match.group(1)
                    parsed_date = self._parse_date_string(date_str)
                    if parsed_date:
                        formatted_date = parsed_date.strftime("%Y-%m-%d")
                        logger.info(
                            f"Extracted date from caption: {formatted_date}"
                        )
                        return formatted_date

            logger.warning("No valid date found in caption")
            return None

        except Exception as e:
            logger.error(f"Error extracting date from caption: {e}")
            return None

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string in various formats.

        Args:
            date_str: Date string to parse

        Returns:
            Parsed datetime object or None if parsing fails
        """
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%m-%d-%Y",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def generate_filename(
        self,
        partner_id: int,
        chat_id: str,
        file_unique_id: str,
        file_path: Optional[str] = None,
    ) -> str:
        """
        Generate a unique filename for the receipt.

        Args:
            partner_id: Partner ID
            chat_id: Telegram chat ID
            file_unique_id: Telegram file unique ID
            file_path: Original file path (to extract extension)

        Returns:
            Generated filename
        """
        # Extract file extension
        file_extension = "jpg"  # Default extension
        if file_path:
            try:
                file_extension = file_path.split(".")[-1].lower()
            except (IndexError, AttributeError):
                file_extension = "jpg"

        filename = (
            f"receipt_{partner_id}_{chat_id}_{file_unique_id}.{file_extension}"
        )
        logger.info(f"Generated filename: {filename}")
        return filename

    def build_notes(
        self,
        caption: str = "",
        extraction_source: str = "manual",
        additional_info: Dict = None,
    ) -> str:
        """
        Build comprehensive notes for the receipt.

        Args:
            caption: User-provided caption
            extraction_source: Source of data extraction ('manual', 'ocr', 'hybrid')
            additional_info: Additional information to include

        Returns:
            Formatted notes string
        """
        notes_parts = []

        # Add caption if provided
        if caption:
            notes_parts.append(f"Caption: {caption}")

        # Add extraction method
        extraction_messages = {
            "manual": "Datos extraídos manualmente del caption",
            "ocr": "Datos extraídos automáticamente via OCR",
            "hybrid": "Datos combinados: OCR + caption del usuario",
        }

        if extraction_source in extraction_messages:
            notes_parts.append(extraction_messages[extraction_source])

        # Add additional info if provided
        if additional_info:
            for key, value in additional_info.items():
                if value:
                    notes_parts.append(f"{key}: {value}")

        # Always add source
        notes_parts.append("Subido via Telegram Bot")

        final_notes = " | ".join(notes_parts)
        logger.info(
            f"Built notes: {final_notes[:100]}..."
        )  # Log first 100 chars
        return final_notes

    def prepare_receipt_data(
        self,
        caption: str,
        partner_id: int,
        chat_id: str,
        file_unique_id: str,
        file_path: Optional[str] = None,
    ) -> Tuple[float, str, str, str]:
        """
        Extract all receipt data and prepare for upload.

        Args:
            caption: User-provided caption
            partner_id: Partner ID
            chat_id: Telegram chat ID
            file_unique_id: Telegram file unique ID
            file_path: Original file path

        Returns:
            Tuple of (amount, payment_date, filename, notes)
        """
        logger.info("Starting receipt data preparation...")

        # Extract data from caption
        caption_data = self.extract_from_caption(caption)

        # Use extracted data or defaults
        amount = caption_data["amount"] or self.default_amount
        payment_date = caption_data["date"] or self.default_date

        # Generate filename
        filename = self.generate_filename(
            partner_id, chat_id, file_unique_id, file_path
        )

        # Determine extraction source
        extraction_source = (
            "manual"
            if caption_data["amount"] or caption_data["date"]
            else "default"
        )

        # Build notes
        notes = self.build_notes(
            caption=caption,
            extraction_source=extraction_source,
            additional_info={
                "Monto detectado": f"S/ {amount:.2f}"
                if caption_data["amount"]
                else None,
                "Fecha detectada": payment_date
                if caption_data["date"]
                else None,
            },
        )

        logger.info(
            f"Receipt data prepared - Amount: {amount}, Date: {payment_date}, "
            f"Filename: {filename}"
        )

        return amount, payment_date, filename, notes

    def validate_extracted_data(
        self, amount: float, payment_date: str
    ) -> Dict[str, bool]:
        """
        Validate the extracted data for reasonableness.

        Args:
            amount: Extracted amount
            payment_date: Extracted date

        Returns:
            Dict with validation results
        """
        validation_results = {
            "amount_valid": False,
            "date_valid": False,
            "overall_valid": False,
        }

        try:
            # Validate amount
            if 0.01 <= amount <= 999999.99:
                validation_results["amount_valid"] = True

            # Validate date
            try:
                date_obj = datetime.strptime(payment_date, "%Y-%m-%d")
                # Check if date is reasonable (not too far in past/future)
                today = datetime.now()
                days_diff = abs((today - date_obj).days)
                if days_diff <= 3650:  # Within 10 years
                    validation_results["date_valid"] = True
            except ValueError:
                pass

            # Overall validation
            validation_results["overall_valid"] = (
                validation_results["amount_valid"]
                and validation_results["date_valid"]
            )

            logger.info(f"Data validation results: {validation_results}")
            return validation_results

        except Exception as e:
            logger.error(f"Error validating extracted data: {e}")
            return validation_results

    def get_extraction_confidence(self, caption: str) -> Dict[str, float]:
        """
        Calculate confidence scores for extracted data.

        Args:
            caption: User caption

        Returns:
            Dict with confidence scores (0.0 to 1.0)
        """
        if not caption:
            return {"amount": 0.0, "date": 0.0, "overall": 0.0}

        confidence_scores = {"amount": 0.0, "date": 0.0}

        # Amount confidence based on explicit keywords and format
        amount_indicators = [
            "monto",
            "pago",
            "importe",
            "cantidad",
            "total",
            "s/",
        ]
        if any(indicator in caption.lower() for indicator in amount_indicators):
            confidence_scores["amount"] += 0.5

        # Check for decimal format
        if re.search(r"\d+[.,]\d{2}", caption):
            confidence_scores["amount"] += 0.3
        elif re.search(r"\d+", caption):
            confidence_scores["amount"] += 0.2

        # Date confidence based on explicit keywords and format
        date_indicators = ["fecha", "date"]
        if any(indicator in caption.lower() for indicator in date_indicators):
            confidence_scores["date"] += 0.5

        # Check for date formats
        if re.search(r"\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4}", caption):
            confidence_scores["date"] += 0.5

        # Overall confidence
        confidence_scores["overall"] = (
            confidence_scores["amount"] + confidence_scores["date"]
        ) / 2

        # Cap at 1.0
        for key in confidence_scores:
            confidence_scores[key] = min(confidence_scores[key], 1.0)

        logger.info(f"Extraction confidence scores: {confidence_scores}")
        return confidence_scores
