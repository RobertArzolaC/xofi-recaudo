"""Service to authenticate partners."""
import logging
from typing import Optional

from apps.partners.models import Partner

logger = logging.getLogger(__name__)


class PartnerAuthenticationService:
    """Service to authenticate partners via document and birth year."""

    @staticmethod
    def authenticate(document_number: str, birth_year: str) -> Optional[Partner]:
        """
        Authenticate a partner using document number and birth year.

        Args:
            document_number: Partner's document number
            birth_year: Partner's birth year (4 digits)

        Returns:
            Partner instance if authenticated, None otherwise
        """
        try:
            # Find partner by document number
            partner = Partner.objects.get(document_number=document_number)

            # Verify birth year
            if partner.birth_date and str(partner.birth_date.year) == birth_year:
                logger.info(f"Partner {partner.id} authenticated successfully")
                return partner

            logger.warning(f"Birth year mismatch for document {document_number}")
            return None
        except Partner.DoesNotExist:
            logger.warning(f"Partner with document {document_number} not found")
            return None
