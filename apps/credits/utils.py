import calendar
from decimal import Decimal

from django.utils import timezone

from apps.credits import choices, models


def add_months(sourcedate, months):
    """Add a given number of months to a date, handling month end properly."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return timezone.datetime(year, month, day).date()


def calculate_and_apply_delinquency_interest(installment) -> Decimal:
    """
    Calculate and apply delinquency interest for an overdue installment.

    This function calculates interest based on:
    - Credit's delinquency rate
    - Days overdue
    - Outstanding installment amount

    Args:
        installment: The overdue installment

    Returns:
        Decimal: Amount of interest applied
    """
    credit = installment.credit

    # If no delinquency rate is set, return 0
    if not credit.delinquency_rate or credit.delinquency_rate == 0:
        return Decimal("0.00")

    # Calculate days overdue
    days_overdue = installment.days_overdue
    if days_overdue <= 0:
        return Decimal("0.00")

    # Get the outstanding amount for this installment
    outstanding_amount = installment.remaining_balance
    if outstanding_amount <= 0:
        return Decimal("0.00")

    # Calculate daily delinquency rate (annual rate / 365)
    annual_rate = credit.delinquency_rate / Decimal("100")
    daily_rate = annual_rate / Decimal("365")

    # Calculate interest: principal * daily_rate * days_overdue
    interest_amount = outstanding_amount * daily_rate * Decimal(str(days_overdue))
    interest_amount = interest_amount.quantize(
        Decimal("0.01"), rounding="ROUND_HALF_UP"
    )

    # Update the installment with delinquency interest
    # Note: This adds to the installment amount, increasing what the customer owes
    installment.installment_amount += interest_amount
    installment.notes = (
        (f"{installment.notes}\n" if installment.notes else "")
        + f"Delinquency interest applied: ${interest_amount} "
        f"({days_overdue} days overdue at {credit.delinquency_rate}% annual rate) "
        f"on {timezone.now().date()}"
    )

    installment.save(update_fields=["installment_amount", "notes", "modified"])

    # Also update the credit's outstanding balance
    credit.outstanding_balance += interest_amount
    credit.save(update_fields=["outstanding_balance", "modified"])

    return interest_amount


def generate_payment_schedule(
    amount: Decimal,
    interest_rate: Decimal,
    term_duration: int,
    payment_frequency: str,
    start_date=None,
) -> dict:
    """
    Generate a payment schedule for a credit.

    Args:
        amount: Credit amount
        interest_rate: Annual interest rate percentage
        term_duration: Duration in months
        payment_frequency: Payment frequency
        start_date: Start date for the schedule (defaults to today)

    Returns:
        dict: Payment schedule with installment details
    """

    if start_date is None:
        start_date = timezone.now().date()

    # Determine payment frequency and number of payments
    payment_periods = {
        choices.PaymentFrequency.WEEKLY: 52,
        choices.PaymentFrequency.BIWEEKLY: 26,
        choices.PaymentFrequency.MONTHLY: 12,
        choices.PaymentFrequency.QUARTERLY: 4,
        choices.PaymentFrequency.ANNUALLY: 1,
    }

    periods_per_year = payment_periods.get(payment_frequency, 12)
    total_periods = (term_duration * periods_per_year) // 12

    # Calculate period interest rate
    annual_rate = interest_rate / Decimal("100")
    period_rate = annual_rate / periods_per_year

    # Calculate fixed payment amount using PMT formula
    if period_rate == 0:
        payment_amount = amount / total_periods
    else:
        payment_amount = amount * period_rate * (1 + period_rate) ** total_periods
        payment_amount = payment_amount / ((1 + period_rate) ** total_periods - 1)
        payment_amount = payment_amount.quantize(
            Decimal("0.01"), rounding="ROUND_HALF_UP"
        )

    # Create payment schedule
    schedule = []
    remaining_balance = amount

    # Determine days between payments based on frequency
    days_between_payments = {
        choices.PaymentFrequency.WEEKLY: 7,
        choices.PaymentFrequency.BIWEEKLY: 14,
        choices.PaymentFrequency.MONTHLY: 30,
        choices.PaymentFrequency.QUARTERLY: 90,
        choices.PaymentFrequency.ANNUALLY: 365,
    }
    days_interval = days_between_payments.get(payment_frequency, 30)

    for period in range(1, total_periods + 1):
        # Calculate payment date
        if payment_frequency == choices.PaymentFrequency.MONTHLY:
            # For monthly payments, increment by actual months
            payment_date = add_months(start_date, period)
        else:
            # For other frequencies, add days
            payment_date = start_date + timezone.timedelta(days=period * days_interval)

        # Calculate interest and principal for this period
        interest_payment = remaining_balance * period_rate
        interest_payment = interest_payment.quantize(
            Decimal("0.01"), rounding="ROUND_HALF_UP"
        )

        # Last payment might need adjustment to ensure exact payoff
        if period == total_periods:
            principal_payment = remaining_balance
            payment_amount = principal_payment + interest_payment
        else:
            principal_payment = payment_amount - interest_payment

        # Update remaining balance
        remaining_balance -= principal_payment
        if remaining_balance < Decimal("0.01"):
            remaining_balance = Decimal("0")

        # Add payment to schedule
        schedule.append(
            {
                "period": period,
                "payment_date": payment_date.isoformat(),
                "payment_amount": float(payment_amount),
                "principal": float(principal_payment),
                "interest": float(interest_payment),
                "remaining_balance": float(remaining_balance),
            }
        )

    # Return schedule
    return {
        "credit_amount": float(amount),
        "interest_rate": float(interest_rate),
        "term_duration": term_duration,
        "payment_frequency": payment_frequency,
        "payment_amount": float(payment_amount),
        "total_payments": total_periods,
        "first_payment_date": start_date.isoformat(),
        "schedule": schedule,
    }


def create_credit_with_installments(
    partner,
    product,
    amount: Decimal,
    interest_rate: Decimal,
    term_duration: int,
    payment_frequency: str,
    start_date,
    delinquency_rate: Decimal = None,
    status: str = None,
    application_date=None,
    approval_date=None,
    disbursement_date=None,
    notes: str = "",
    created_by=None,
    application=None,
    payment_schedule: dict = None,
):
    """
    Create a credit with its installments based on the provided parameters.

    This function creates a credit and generates its installment schedule.
    It can be used for new credits, refinancing, rescheduling, etc.

    Args:
        partner: Partner who will receive the credit
        product: Credit product
        amount: Credit amount
        interest_rate: Annual interest rate percentage
        term_duration: Duration in months
        payment_frequency: Payment frequency (monthly, weekly, etc.)
        start_date: Start date for the installment schedule (required)
        delinquency_rate: Delinquency rate percentage (optional)
        status: Credit status (defaults to PENDING)
        application_date: Application date (defaults to today)
        approval_date: Approval date (optional)
        disbursement_date: Disbursement date (optional)
        notes: Additional notes
        created_by: User who creates the credit
        application: Associated credit application (optional)
        payment_schedule: Pre-calculated payment schedule (optional)

    Returns:
        Credit: The created credit object or None if creation failed.
    """

    # Set defaults
    if status is None:
        status = choices.CreditStatus.PENDING
    if application_date is None:
        application_date = timezone.now().date()
    if delinquency_rate is None:
        delinquency_rate = Decimal("0.00")

    # Generate payment schedule if not provided
    if payment_schedule is None:
        payment_schedule = generate_payment_schedule(
            amount=amount,
            interest_rate=interest_rate,
            term_duration=term_duration,
            payment_frequency=payment_frequency,
            start_date=start_date,
        )

    # Calculate payment amount from schedule
    payment_amount = None
    if payment_schedule and "payment_amount" in payment_schedule:
        payment_amount = Decimal(str(payment_schedule["payment_amount"]))

    # Create the credit
    credit = models.Credit.objects.create(
        partner=partner,
        product=product,
        amount=amount,
        interest_rate=interest_rate,
        term_duration=term_duration,
        payment_frequency=payment_frequency,
        status=status,
        application_date=application_date,
        approval_date=approval_date,
        disbursement_date=disbursement_date,
        payment_amount=payment_amount,
        notes=notes,
        created_by=created_by,
        application=application,
        outstanding_balance=amount,
        delinquency_rate=delinquency_rate,
    )

    # Create installments based on the payment schedule
    if payment_schedule and "schedule" in payment_schedule:
        for installment_data in payment_schedule["schedule"]:
            # Convert ISO date string back to date object if needed
            due_date = installment_data["payment_date"]
            if isinstance(due_date, str):
                due_date = timezone.datetime.fromisoformat(due_date).date()

            # Create the installment
            models.Installment.objects.create(
                credit=credit,
                installment_number=installment_data["period"],
                due_date=due_date,
                installment_amount=Decimal(str(installment_data["payment_amount"])),
                principal_amount=Decimal(str(installment_data["principal"])),
                interest_amount=Decimal(str(installment_data["interest"])),
                balance_after=Decimal(str(installment_data["remaining_balance"])),
                created_by=created_by,
            )

    return credit
