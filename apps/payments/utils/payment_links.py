"""
Payment Link Generation Service.

This service generates generic payment links for campaigns and magic payment links.
In the future, this will be integrated with actual payment providers.
"""

import hashlib
import logging
from datetime import timedelta
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


def create_magic_payment_link(
    partner,
    debts: list,
    title: str = None,
    description: str = "",
    hours_to_expire: int = 24,
    user=None,
):
    """
    Create a Magic Payment Link for a partner with multiple debts.

    Args:
        partner: Partner instance
        debts: List of debt objects (Installments, Contributions, SocialSecurity, Penalty)
        title: Optional custom title for the link
        description: Optional description
        hours_to_expire: Hours until the link expires (default 24)
        user: User creating the link (for tracking)

    Returns:
        MagicPaymentLink instance
    """
    from apps.payments.models import MagicPaymentLink

    if not debts:
        raise ValueError("Cannot create magic link without debts")

    # Calculate total amount from all debt types
    total_amount = Decimal("0.00")
    for debt in debts:
        # Get amount based on debt type
        if hasattr(debt, "installment_amount"):  # Installment
            total_amount += debt.installment_amount
        elif hasattr(debt, "amount"):  # Contribution, SocialSecurity, Penalty
            total_amount += debt.amount

    # Generate default title if not provided
    if not title:
        month_name = timezone.now().strftime("%B")
        year = timezone.now().year
        title = f"Pago de deudas - {month_name} de {year} - DNI {partner.document_number}"

    # Generate default description if not provided
    if not description:
        description = f"Magic link rápido para {partner.full_name}"

    # Calculate expiration time
    expires_at = timezone.now() + timedelta(hours=hours_to_expire)

    # Build metadata with debt information
    metadata = {"debts": []}

    for debt in debts:
        debt_type = debt.__class__.__name__.lower()
        debt_amount = (
            debt.installment_amount
            if hasattr(debt, "installment_amount")
            else debt.amount
        )

        debt_info = {
            "type": debt_type,
            "id": debt.id,
            "amount": float(debt_amount),
            "due_date": debt.due_date.isoformat() if hasattr(debt, "due_date") else None,
        }

        # Add type-specific fields
        if debt_type == "installment":
            debt_info["number"] = debt.installment_number
            debt_info["credit_id"] = debt.credit_id
        elif debt_type in ["contribution", "socialsecurity", "penalty"]:
            debt_info["name"] = getattr(debt, "name", str(debt))

        metadata["debts"].append(debt_info)

    # Create the Magic Payment Link
    magic_link = MagicPaymentLink.objects.create(
        partner=partner,
        name=title,
        description=description,
        amount=total_amount,
        expires_at=expires_at,
        metadata=metadata,
        created_by=user,
        modified_by=user,
    )

    logger.info(
        f"Created Magic Payment Link {magic_link.token} for partner {partner.id} "
        f"with {len(debts)} debts totaling {total_amount}"
    )

    return magic_link


def create_magic_link_for_partner_by_document(
    document_number: str,
    hours_to_expire: int = 24,
    include_upcoming: bool = False,
    user=None,
):
    """
    Create a Magic Payment Link for a partner by document number.

    Args:
        document_number: Partner's document number (DNI)
        hours_to_expire: Hours until the link expires (default 24)
        include_upcoming: Whether to include upcoming debts (default False)
        user: User creating the link (for tracking)

    Returns:
        MagicPaymentLink instance or None if partner not found or no debts

    Raises:
        ValueError: If partner not found
    """
    from apps.partners.models import Partner
    from apps.partners.services import PartnerDebtService

    try:
        partner = Partner.objects.get(document_number=document_number)
    except Partner.DoesNotExist:
        raise ValueError(f"Partner with document number {document_number} not found")

    # Get all debts for the partner
    debts = PartnerDebtService.get_partner_debt_objects_for_payment(
        partner, include_upcoming=include_upcoming
    )

    if not debts:
        logger.info(f"No debts found for partner {partner.id}")
        return None

    return create_magic_payment_link(
        partner=partner,
        debts=debts,
        hours_to_expire=hours_to_expire,
        user=user,
    )
