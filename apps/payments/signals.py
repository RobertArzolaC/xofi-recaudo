import logging
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.compliance import choices as compliance_choices
from apps.credits import choices as credit_choices
from apps.credits import models as credit_models
from apps.payments import choices, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.PaymentConceptAllocation)
def update_concept_payment_status(
    sender, instance: models.PaymentConceptAllocation, created: bool, **kwargs
) -> None:
    """
    Signal to update concept payment status when payment allocation is made.

    Args:
        sender: The model class that sent the signal
        instance: The PaymentConceptAllocation instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if not created or instance.payment.status != choices.PaymentStatus.PAID:
        return

    concept_object = instance.concept_object
    if not concept_object:
        return

    # Handle different types of concepts
    if concept_object._meta.model_name == "installment":
        _update_installment_status(concept_object, instance)
    elif concept_object._meta.model_name in [
        "contribution",
        "socialsecurity",
        "penalty",
    ]:
        _update_compliance_status(concept_object, instance)


def _update_installment_status(installment, allocation_instance):
    """
    Update installment payment status.
    """
    # Check if installment is fully paid
    total_paid = installment.amount_paid
    if total_paid >= installment.installment_amount:
        credit_models.Installment.objects.filter(pk=installment.pk).update(
            payment_date=allocation_instance.application_date,
            status=credit_choices.InstallmentStatus.PAID,
        )
        logger.info(
            f"Installment {installment.installment_number} for credit {installment.credit.id} marked as paid"
        )

        # Update credit outstanding balance
        _update_credit_balance(installment.credit)


def _update_compliance_status(compliance_object, allocation_instance):
    """
    Update compliance obligation status.
    """
    if hasattr(compliance_object, "is_fully_paid") and compliance_object.is_fully_paid:
        # Update compliance object status if it has one
        if hasattr(compliance_object, "status"):
            compliance_object.__class__.objects.filter(pk=compliance_object.pk).update(
                status=compliance_choices.ComplianceStatus.PAID,
            )
            logger.info(f"Compliance obligation {compliance_object} marked as paid")


def _update_credit_balance(credit):
    """
    Update credit outstanding balance based on paid installments.
    """
    # Calculate total paid amount for this credit
    total_paid = sum(
        allocation.amount_applied
        for allocation in models.PaymentConceptAllocation.objects.filter(
            content_type__app_label="credits",
            content_type__model="installment",
            object_id__in=credit.installments.values_list("id", flat=True),
            payment__status=choices.PaymentStatus.PAID,
        )
    )

    new_balance = credit.amount - total_paid
    if new_balance < Decimal("0.00"):
        new_balance = Decimal("0.00")

    credit_models.Credit.objects.filter(pk=credit.pk).update(
        outstanding_balance=new_balance
    )

    # Check if credit is fully paid
    if new_balance == Decimal("0.00"):
        credit_models.Credit.objects.filter(pk=credit.pk).update(
            status=credit_choices.CreditStatus.COMPLETED
        )
        logger.info(f"Credit {credit.id} marked as completed - fully paid")

    logger.info(f"Updated outstanding balance for credit {credit.id}: ${new_balance}")


@receiver(post_save, sender=models.Payment)
def update_payment_status_on_allocations(
    sender, instance: models.Payment, created: bool, **kwargs
) -> None:
    """
    Signal to update payment status based on allocations.

    Args:
        sender: The model class that sent the signal
        instance: The Payment instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if not created:
        # Update payment status based on allocations
        if instance.amount > Decimal("0.00"):
            if instance.amount >= instance.total_allocated:
                instance.status = choices.PaymentStatus.PAID
            elif instance.amount > Decimal("0.00"):
                instance.status = choices.PaymentStatus.PARTIAL
            else:
                instance.status = choices.PaymentStatus.PENDING

            # Only save if status actually changed to avoid recursion
            if instance._state.db and hasattr(instance, "_original_status"):
                if instance.status != instance._original_status:
                    models.Payment.objects.filter(pk=instance.pk).update(
                        status=instance.status
                    )
                    logger.info(
                        f"Payment {instance.payment_number} status updated to {instance.status}"
                    )
