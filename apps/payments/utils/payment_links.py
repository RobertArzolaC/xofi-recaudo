import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.partners import models as partner_models
from apps.partners import services as partner_services

logger = logging.getLogger(__name__)


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
            "due_date": debt.due_date.isoformat()
            if hasattr(debt, "due_date")
            else None,
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
        raise ValueError(
            f"Partner with document number {document_number} not found"
        )

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


def create_magic_link_for_partner(
    partner: partner_models.Partner,
    hours_to_expire: int = 24,
    include_upcoming: bool = False,
    user=None,
):
    """
    Create a Magic Payment Link for a partner by ID.

    Args:
        partner_id: Partner's ID
        hours_to_expire: Hours until the link expires (default 24)
        include_upcoming: Whether to include upcoming debts (default False)
        user: User creating the link (for tracking)
    Returns:
        MagicPaymentLink instance or None if no debts

    Raises:
        ValueError: If partner not found
    """

    # Get all debts for the partner
    debts = partner_services.PartnerDebtService.get_partner_debt_objects_for_payment(
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
