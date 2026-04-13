from typing import Dict

from constance import config

from apps.notifications.models import CampaignNotification


def prepare_message_context(
    notification: "CampaignNotification", debt_detail: Dict
) -> dict:
    """
    Prepare context dictionary for message rendering.

    Args:
        notification: CampaignNotification instance
        debt_detail: Dictionary with partner debt details

    Returns:
        dict: Context dictionary for template rendering
    """
    recipient = notification.recipient
    campaign = notification.campaign

    context = {
        "partner_name": recipient.full_name,
        "debt_amount": f"S/ {notification.total_debt_amount:,.2f}",
        "payment_link": notification.payment_link_url or "",
        "campaign_name": getattr(campaign, "name", ""),
        "company_name": config.PROJECT_NAME,
        "contact_phone": f"+51 {config.COMPANY_PHONE}",
        "notification_type": notification.get_notification_type_display(),
    }

    # Support specific CSV contact fields if applicable
    if hasattr(recipient, 'amount'):
        context["full_name"] = recipient.full_name
        context["amount"] = f"{recipient.amount:,.2f}"
    
    if hasattr(recipient, 'additional_data') and isinstance(recipient.additional_data, dict):
        # Expose all additional data keys into the context
        for key, val in recipient.additional_data.items():
            context[key] = str(val)

    # Add detailed debt information
    if debt_detail["credit_debt"] > 0:
        context["credit_debt"] = f"S/ {debt_detail['credit_debt']:,.2f}"
        context["credit_debt_count"] = debt_detail["overdue_installments"]
    else:
        context["credit_debt"] = ""
        context["credit_debt_count"] = 0

    if debt_detail["contribution_debt"] > 0:
        context["contribution_debt"] = (
            f"S/ {debt_detail['contribution_debt']:,.2f}"
        )
        context["contribution_debt_count"] = debt_detail[
            "overdue_contributions"
        ]
    else:
        context["contribution_debt"] = ""
        context["contribution_debt_count"] = 0

    if debt_detail["social_security_debt"] > 0:
        context["social_security_debt"] = (
            f"S/ {debt_detail['social_security_debt']:,.2f}"
        )
        context["social_security_debt_count"] = debt_detail[
            "overdue_social_security"
        ]
    else:
        context["social_security_debt"] = ""
        context["social_security_debt_count"] = 0

    if debt_detail["penalty_debt"] > 0:
        context["penalty_debt"] = f"S/ {debt_detail['penalty_debt']:,.2f}"
        context["penalty_debt_count"] = debt_detail["overdue_penalties"]
    else:
        context["penalty_debt"] = ""
        context["penalty_debt_count"] = 0

    return context


def generate_default_message(
    notification: "CampaignNotification",
    context: Dict,
    debt_detail: Dict,
) -> str:
    """
    Generate a default message when no template is available.

    Args:
        notification: CampaignNotification instance
        context: Message context dictionary
        debt_detail: Dictionary with partner debt details

    Returns:
        str: Generated default message
    """
    message_parts = [
        f"Hola {context['partner_name']},",
        "",
        f"Le recordamos que tiene obligaciones pendientes por un total de {context['debt_amount']}.",
        "",
        "📋 *Detalle de sus obligaciones:*",
    ]

    # Add credit debt details if exists
    if debt_detail["credit_debt"] > 0:
        message_parts.append(
            f"💳 Cuotas de crédito: {context['credit_debt']} ({context['credit_debt_count']} cuota(s))"
        )

    # Add contribution debt details if exists
    if debt_detail["contribution_debt"] > 0:
        message_parts.append(
            f"📊 Aportaciones: {context['contribution_debt']} ({context['contribution_debt_count']} aportación(es))"
        )

    # Add social security debt details if exists
    if debt_detail["social_security_debt"] > 0:
        message_parts.append(
            f"🏥 Previsión Social: {context['social_security_debt']} ({context['social_security_debt_count']} obligación(es))"
        )

    # Add penalty debt details if exists
    if debt_detail["penalty_debt"] > 0:
        message_parts.append(
            f"⚠️ Penalidades: {context['penalty_debt']} ({context['penalty_debt_count']} penalidad(es))"
        )

    message_parts.append("")

    if notification.included_payment_link and notification.payment_link_url:
        message_parts.extend(
            [
                "💰 Puede realizar su pago de forma rápida y segura:",
                f"👉 {notification.payment_link_url}",
                "",
            ]
        )

    message_parts.extend(
        [
            "Para más información, contáctenos:",
            f"📞 {context['contact_phone']}",
            "",
            "Gracias por su atención.",
            f"Atentamente, *{context['company_name']}*",
        ]
    )

    return "\n".join(message_parts)
