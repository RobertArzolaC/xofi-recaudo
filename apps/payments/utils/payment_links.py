"""
Payment Link Generation Service.

This service generates generic payment links for campaigns.
In the future, this will be integrated with actual payment providers.
"""

import hashlib
import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.utils import timezone
from django.utils.encoding import force_bytes

logger = logging.getLogger(__name__)


def generate_payment_link(
    partner_id: int,
    amount: Decimal,
    campaign_id: Optional[int] = None,
    reference: Optional[str] = None,
) -> str:
    """
    Generate a generic payment link for a partner.

    Args:
        partner_id: ID of the partner who will make the payment
        amount: Payment amount
        campaign_id: Optional campaign ID associated with this payment
        reference: Optional reference or description

    Returns:
        str: Generated payment link URL
    """
    base_url = settings.PAYMENT_LINK_BASE_URL

    # Generate a unique token for this payment link
    token = _generate_payment_token(partner_id, amount, campaign_id)

    # Build query parameters
    params = [
        f"partner={partner_id}",
        f"amount={amount}",
        f"token={token}",
    ]

    if campaign_id:
        params.append(f"campaign={campaign_id}")

    if reference:
        params.append(f"ref={reference}")

    # Construct the full URL
    payment_url = f"{base_url}?{'&'.join(params)}"

    logger.info(f"Generated payment link for partner {partner_id}: {payment_url}")

    return payment_url


def generate_payment_link_for_debt(
    partner_id: int,
    debt_amount: Decimal,
    campaign_id: Optional[int] = None,
) -> str:
    """
    Generate a payment link for partner's outstanding debt.

    Args:
        partner_id: ID of the partner
        debt_amount: Total debt amount
        campaign_id: Optional campaign ID

    Returns:
        str: Payment link URL
    """
    reference = f"Pago de deuda - Socio {partner_id}"
    return generate_payment_link(
        partner_id=partner_id,
        amount=debt_amount,
        campaign_id=campaign_id,
        reference=reference,
    )


def _generate_payment_token(
    partner_id: int, amount: Decimal, campaign_id: Optional[int] = None
) -> str:
    """
    Generate a unique token for the payment link.

    This token can be used to verify the authenticity of the payment link.

    Args:
        partner_id: Partner ID
        amount: Payment amount
        campaign_id: Optional campaign ID

    Returns:
        str: Generated token (first 16 characters of hash)
    """
    # Create a string with the payment details
    timestamp = timezone.now().isoformat()
    data = f"{partner_id}:{amount}:{campaign_id}:{timestamp}:{settings.SECRET_KEY}"

    # Generate SHA256 hash
    hash_obj = hashlib.sha256(force_bytes(data))
    token = hash_obj.hexdigest()[:16]  # Use first 16 characters

    return token


def get_payment_page_url() -> str:
    """
    Get the base payment page URL.

    Returns:
        str: Base payment page URL
    """
    return settings.PAYMENT_LINK_BASE_URL
