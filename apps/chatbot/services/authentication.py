import logging
import re
from typing import Optional

from apps.partners.models import Partner

logger = logging.getLogger(__name__)


class PartnerAuthenticationService:
    """Service to authenticate partners via document and birth year."""

    @staticmethod
    def authenticate(
        document_number: str, birth_year: str
    ) -> Optional[Partner]:
        """
        Authenticate a partner using document number and birth year.

        Args:
            document_number: Partner's document number
            birth_year: Partner's birth year (4 digits)

        Returns:
            Partner instance if authenticated, None otherwise
        """
        try:
            partner = Partner.objects.get(document_number=document_number)

            if (
                partner.birth_date
                and str(partner.birth_date.year) == birth_year
            ):
                logger.info(f"Partner {partner.id} authenticated successfully")
                return partner

            logger.warning(
                f"Birth year mismatch for document {document_number}"
            )
            return None
        except Partner.DoesNotExist:
            logger.warning(f"Partner with document {document_number} not found")
            return None

    @staticmethod
    def is_authentication_message(message: str) -> bool:
        """
        Check if message matches the authentication pattern.
        Expected: document_number and birth_year (e.g., "12345678 1990")
        """
        pattern = r"\b\d{8}\s+\d{4}\b"
        return bool(re.search(pattern, message))

    @staticmethod
    def extract_auth_data(message: str) -> Optional[dict]:
        """
        Extract authentication data from message.

        Returns:
            Dict with document_number and birth_year or None
        """
        pattern = r"\b(\d{8})\s+(\d{4})\b"
        match = re.search(pattern, message)
        if match:
            return {
                "document_number": match.group(1),
                "birth_year": match.group(2),
            }
        return None
