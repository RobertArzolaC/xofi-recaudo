import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.compliance import choices as compliance_choices
from apps.compliance import models as compliance_models
from apps.credits import choices as credit_choices
from apps.credits import models as credit_models
from apps.payments import choices, models


def process_payment_for_multiple_concepts(
    partner,
    payment_amount: Decimal,
    concepts_data: List[Dict[str, Any]],
    payment_method: str = choices.PaymentMethod.CASH,
    reference_number: str = "",
    notes: str = "",
    payment_number: Optional[str] = None,
) -> Tuple[models.Payment, List[models.PaymentConceptAllocation]]:
    """
    Process a payment that covers multiple concepts (installments, obligations, etc.).

    Args:
        partner: Partner making the payment
        payment_amount: Total payment amount
        concepts_data: List of dicts with 'concept_object', 'amount', and optionally 'notes'
        payment_method: Method used for payment
        reference_number: Reference number for the payment
        notes: General notes for the payment
        payment_number: Optional custom payment number

    Returns:
        Tuple of (Payment instance, list of PaymentConceptAllocation instances)
    """
    total_allocation = sum(Decimal(str(concept["amount"])) for concept in concepts_data)

    if total_allocation > payment_amount:
        raise ValueError("Total allocation amount exceeds payment amount")

    if not payment_number:
        payment_number = f"PAY-{partner.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}"

    with transaction.atomic():
        # Create the main payment record
        payment = models.Payment.objects.create(
            partner=partner,
            payment_number=payment_number,
            payment_date=timezone.now().date(),
            amount=payment_amount,
            payment_method=payment_method,
            reference_number=reference_number,
            status=choices.PaymentStatus.PAID,
            notes=notes,
        )

        # Create allocations for each concept
        allocations = []
        for concept_data in concepts_data:
            concept_object = concept_data["concept_object"]
            amount = Decimal(str(concept_data["amount"]))
            concept_notes = concept_data.get("notes", "")

            allocation = (
                models.PaymentConceptAllocation.objects.allocate_payment_to_concept(
                    payment=payment,
                    concept_object=concept_object,
                    amount_applied=amount,
                    allocation_type=choices.AllocationStatus.FULL
                    if amount == getattr(concept_object, "amount", amount)
                    else choices.AllocationStatus.PARTIAL,
                    notes=concept_notes,
                )
            )
            allocations.append(allocation)

        return payment, allocations


def split_payment_across_installments(
    installments: List, payment_amount: Decimal, strategy: str = "chronological"
) -> List[Dict[str, Any]]:
    """
    Split a payment amount across multiple installments using different strategies.

    Args:
        installments: List of installment objects
        payment_amount: Total amount to split
        strategy: Strategy for splitting ('chronological', 'proportional', 'equal')

    Returns:
        List of dicts with installment allocation data
    """
    if strategy == "chronological":
        return _split_chronological(installments, payment_amount)
    elif strategy == "proportional":
        return _split_proportional(installments, payment_amount)
    elif strategy == "equal":
        return _split_equal(installments, payment_amount)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def _split_chronological(
    installments: List, payment_amount: Decimal
) -> List[Dict[str, Any]]:
    """Split payment chronologically (oldest installments first)."""
    # Sort by due date
    sorted_installments = sorted(installments, key=lambda x: x.due_date)

    allocations = []
    remaining_amount = payment_amount

    for installment in sorted_installments:
        if remaining_amount <= 0:
            break

        # Get remaining balance for this installment
        installment_balance = getattr(
            installment, "remaining_balance", installment.installment_amount
        )

        # Allocate up to the installment balance or remaining payment amount
        allocation_amount = min(remaining_amount, installment_balance)

        allocations.append(
            {
                "concept_object": installment,
                "amount": allocation_amount,
                "notes": f"Chronological allocation - {allocation_amount} of {installment_balance}",
            }
        )

        remaining_amount -= allocation_amount

    return allocations


def _split_proportional(
    installments: List, payment_amount: Decimal
) -> List[Dict[str, Any]]:
    """Split payment proportionally based on installment amounts."""
    total_installment_amount = sum(
        getattr(inst, "remaining_balance", inst.installment_amount)
        for inst in installments
    )

    if total_installment_amount == 0:
        raise ValueError("Total installment amount is zero")

    allocations = []
    remaining_amount = payment_amount

    for i, installment in enumerate(installments):
        installment_balance = getattr(
            installment, "remaining_balance", installment.installment_amount
        )

        # Calculate proportional amount
        if i == len(installments) - 1:  # Last installment gets remaining amount
            allocation_amount = remaining_amount
        else:
            proportion = installment_balance / total_installment_amount
            allocation_amount = (payment_amount * proportion).quantize(Decimal("0.01"))

        # Ensure we don't exceed installment balance
        allocation_amount = min(allocation_amount, installment_balance)

        if allocation_amount > 0:
            allocations.append(
                {
                    "concept_object": installment,
                    "amount": allocation_amount,
                    "notes": f"Proportional allocation - {allocation_amount} of {installment_balance}",
                }
            )

            remaining_amount -= allocation_amount

    return allocations


def _split_equal(installments: List, payment_amount: Decimal) -> List[Dict[str, Any]]:
    """Split payment equally among installments."""
    if not installments:
        return []

    equal_amount = payment_amount / len(installments)
    equal_amount = equal_amount.quantize(Decimal("0.01"))

    allocations = []
    remaining_amount = payment_amount

    for i, installment in enumerate(installments):
        installment_balance = getattr(
            installment, "remaining_balance", installment.installment_amount
        )

        # Last installment gets remaining amount to handle rounding
        if i == len(installments) - 1:
            allocation_amount = remaining_amount
        else:
            allocation_amount = min(equal_amount, installment_balance)

        if allocation_amount > 0:
            allocations.append(
                {
                    "concept_object": installment,
                    "amount": allocation_amount,
                    "notes": f"Equal allocation - {allocation_amount} of {installment_balance}",
                }
            )

            remaining_amount -= allocation_amount

    return allocations


def calculate_payment_summary(
    partner, period_start=None, period_end=None
) -> Dict[str, Any]:
    """
    Calculate payment summary for a partner within a given period.

    Args:
        partner: Partner object
        period_start: Start date for the period (optional)
        period_end: End date for the period (optional)

    Returns:
        Dictionary with payment summary data
    """
    payments_query = models.Payment.objects.for_partner(partner)

    if period_start:
        payments_query = payments_query.filter(payment_date__gte=period_start)
    if period_end:
        payments_query = payments_query.filter(payment_date__lte=period_end)

    summary = {
        "total_scheduled": Decimal("0.00"),
        "total_paid": Decimal("0.00"),
        "total_pending": Decimal("0.00"),
        "total_overdue": Decimal("0.00"),
        "payment_count": 0,
        "overdue_count": 0,
        "by_concept": {},
        "by_status": {},
    }

    for payment in payments_query:
        summary["total_scheduled"] += payment.scheduled_amount
        summary["total_paid"] += payment.paid_amount
        summary["payment_count"] += 1

        if payment.status == choices.PaymentStatus.PENDING:
            summary["total_pending"] += payment.remaining_amount

        if payment.is_overdue:
            summary["total_overdue"] += payment.remaining_amount
            summary["overdue_count"] += 1

        # Group by concept
        concept = payment.get_concept_display()
        if concept not in summary["by_concept"]:
            summary["by_concept"][concept] = {
                "scheduled": Decimal("0.00"),
                "paid": Decimal("0.00"),
                "count": 0,
            }
        summary["by_concept"][concept]["scheduled"] += payment.scheduled_amount
        summary["by_concept"][concept]["paid"] += payment.paid_amount
        summary["by_concept"][concept]["count"] += 1

        # Group by status
        status = payment.get_status_display()
        if status not in summary["by_status"]:
            summary["by_status"][status] = {
                "scheduled": Decimal("0.00"),
                "paid": Decimal("0.00"),
                "count": 0,
            }
        summary["by_status"][status]["scheduled"] += payment.scheduled_amount
        summary["by_status"][status]["paid"] += payment.paid_amount
        summary["by_status"][status]["count"] += 1

    return summary


def create_payment_schedule_from_installments(credit) -> List[models.Payment]:
    """
    Create payment records for all installments in a credit.

    Args:
        credit: Credit object with installments

    Returns:
        List of created Payment objects
    """
    payments = []

    with transaction.atomic():
        for installment in credit.installments.all():
            payment = models.Payment.create_for_installment(installment)
            payments.append(payment)

    return payments


def auto_allocate_payment_to_best_match(
    payment: models.Payment, available_concepts: List
) -> Optional[models.PaymentConceptAllocation]:
    """
    Automatically allocate a payment to the best matching concept based on business rules.

    Args:
        payment: Payment object to allocate
        available_concepts: List of available concept objects

    Returns:
        PaymentConceptAllocation if allocation was successful, None otherwise
    """
    if not available_concepts:
        return None

    # Filter concepts that match the payment type
    compatible_concepts = []
    for concept in available_concepts:
        valid, _ = payment.can_be_allocated_to_concept(concept)
        if valid:
            compatible_concepts.append(concept)

    if not compatible_concepts:
        return None

    # Business rules for auto-allocation:
    # 1. Exact amount match takes priority
    # 2. Overdue obligations take priority
    # 3. Oldest due date takes priority

    best_match = None
    best_score = -1

    for concept in compatible_concepts:
        score = 0
        concept_amount = getattr(
            concept, "remaining_balance", getattr(concept, "amount", 0)
        )

        # Exact amount match gets highest priority
        if concept_amount == payment.unallocated_amount:
            score += 1000

        # Overdue concepts get priority
        if hasattr(concept, "is_overdue") and concept.is_overdue:
            score += 100

        # Older due dates get priority
        if hasattr(concept, "due_date") and concept.due_date:
            days_old = (timezone.now().date() - concept.due_date).days
            score += min(days_old, 50)  # Cap at 50 points

        if score > best_score:
            best_score = score
            best_match = concept

    if best_match:
        concept_amount = getattr(
            best_match, "remaining_balance", getattr(best_match, "amount", 0)
        )
        allocation_amount = min(payment.unallocated_amount, concept_amount)

        return payment.allocate_to_concept(
            concept_object=best_match,
            amount=allocation_amount,
            notes="Auto-allocated based on business rules",
        )

    return None


def get_partner_pending_debts(partner) -> List[Dict[str, Any]]:
    """
    Get all pending debts for a partner across different modules.

    Args:
        partner: Partner object

    Returns:
        List of dictionaries with debt information
    """
    pending_debts = []

    # Try to get installments from credits app if it exists
    try:
        pending_installments = credit_models.Installment.objects.filter(
            credit__partner=partner,
            credit__status=credit_choices.CreditStatus.ACTIVE,
            status__in=[
                credit_choices.InstallmentStatus.PENDING,
                credit_choices.InstallmentStatus.OVERDUE,
                credit_choices.InstallmentStatus.PARTIAL,
            ],
        ).order_by("due_date")[:3]

        for installment in pending_installments:
            debt = {
                "type": _("Installment"),
                "slug": "installment",
                "id": installment.id,
                "description": f"{_('Installment')} #{installment.installment_number} - {(_('Credit'))} {installment.credit.id}",
                "due_date": installment.due_date,
                "amount": installment.remaining_balance
                if hasattr(installment, "remaining_balance")
                else installment.installment_amount,
                "is_overdue": installment.is_overdue
                if hasattr(installment, "is_overdue")
                else False,
                "days_overdue": (timezone.now().date() - installment.due_date).days
                if installment.due_date
                and hasattr(installment, "is_overdue")
                and installment.is_overdue
                else 0,
            }
            pending_debts.append(debt)
    except ImportError:
        pass  # Credits app not available

    # Try to get compliance obligations if compliance app exists
    try:
        # Contributions
        pending_contributions = compliance_models.Contribution.objects.filter(
            partner=partner,
            status__in=[
                compliance_choices.ComplianceStatus.PENDING,
                compliance_choices.ComplianceStatus.OVERDUE,
                compliance_choices.ComplianceStatus.PARTIAL,
            ],
        )

        for contribution in pending_contributions:
            debt = {
                "type": _("Contribution"),
                "slug": "contribution",
                "id": contribution.id,
                "description": f"{_('Contribution')} - {contribution.period_display}",
                "due_date": contribution.due_date,
                "amount": contribution.remaining_balance
                if hasattr(contribution, "remaining_balance")
                else contribution.amount,
                "is_overdue": contribution.is_overdue
                if hasattr(contribution, "is_overdue")
                else False,
                "days_overdue": (timezone.now().date() - contribution.due_date).days
                if contribution.due_date
                and hasattr(contribution, "is_overdue")
                and contribution.is_overdue
                else 0,
            }
            pending_debts.append(debt)

        # Social Security
        pending_social_security = compliance_models.SocialSecurity.objects.filter(
            partner=partner,
            status__in=[
                compliance_choices.ComplianceStatus.PENDING,
                compliance_choices.ComplianceStatus.OVERDUE,
                compliance_choices.ComplianceStatus.PARTIAL,
            ],
        )

        for ss in pending_social_security:
            debt = {
                "type": _("Social Security"),
                "slug": "social_security",
                "id": ss.id,
                "description": f"{_('Social Security')} - {ss.period_display}",
                "due_date": ss.due_date,
                "amount": ss.remaining_balance
                if hasattr(ss, "remaining_balance")
                else ss.amount,
                "is_overdue": ss.is_overdue if hasattr(ss, "is_overdue") else False,
                "days_overdue": (timezone.now().date() - ss.due_date).days
                if ss.due_date and hasattr(ss, "is_overdue") and ss.is_overdue
                else 0,
            }
            pending_debts.append(debt)

        # Penalties
        pending_penalties = compliance_models.Penalty.objects.filter(
            partner=partner,
            status__in=[
                compliance_choices.ComplianceStatus.PENDING,
                compliance_choices.ComplianceStatus.OVERDUE,
                compliance_choices.ComplianceStatus.PARTIAL,
            ],
        )

        for penalty in pending_penalties:
            debt = {
                "type": _("Penalty"),
                "slug": "penalty",
                "id": penalty.id,
                "description": f"{_('Penalty')} - {penalty.description}",
                "due_date": penalty.due_date,
                "amount": penalty.remaining_balance
                if hasattr(penalty, "remaining_balance")
                else penalty.amount,
                "is_overdue": penalty.is_overdue
                if hasattr(penalty, "is_overdue")
                else False,
                "days_overdue": (timezone.now().date() - penalty.due_date).days
                if penalty.due_date
                and hasattr(penalty, "is_overdue")
                and penalty.is_overdue
                else 0,
            }
            pending_debts.append(debt)

    except ImportError:
        pass  # Compliance app not available

    # Sort by due date, with overdue items first
    pending_debts.sort(
        key=lambda x: (
            not x["is_overdue"],
            x["due_date"] or timezone.now().date(),
        )
    )

    return pending_debts


def generate_order_number():
    """Genera un número de orden único"""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"ord_live_{timestamp}{random_suffix}"
