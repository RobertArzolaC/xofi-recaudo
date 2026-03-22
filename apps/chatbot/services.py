"""
Chatbot Dashboard Services
Servicios para calcular métricas y estadísticas del chatbot
"""
import json
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone


def get_chatbot_kpis():
    """
    KPIs principales del chatbot: conversaciones, mensajes, autenticaciones.
    """
    from apps.chatbot.models import AgentConversation, ConversationMessage
    from apps.chatbot.choices import ConversationStatus

    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_30_days = today - timedelta(days=30)

    try:
        total_conversations = AgentConversation.objects.count()
    except Exception:
        total_conversations = 0

    try:
        active_conversations = AgentConversation.objects.filter(
            status=ConversationStatus.ACTIVE
        ).count()
    except Exception:
        active_conversations = 0

    try:
        authenticated_conversations = AgentConversation.objects.filter(
            authenticated=True
        ).count()
    except Exception:
        authenticated_conversations = 0

    try:
        auth_rate = (
            round((authenticated_conversations / total_conversations) * 100, 1)
            if total_conversations > 0
            else 0
        )
    except Exception:
        auth_rate = 0

    try:
        messages_this_month = ConversationMessage.objects.filter(
            created__date__gte=this_month
        ).count()
    except Exception:
        messages_this_month = 0

    try:
        new_conversations_30d = AgentConversation.objects.filter(
            created__date__gte=last_30_days
        ).count()
    except Exception:
        new_conversations_30d = 0

    try:
        whatsapp_count = AgentConversation.objects.filter(
            channel="WHATSAPP"
        ).count()
    except Exception:
        whatsapp_count = 0

    try:
        telegram_count = AgentConversation.objects.filter(
            channel="TELEGRAM"
        ).count()
    except Exception:
        telegram_count = 0

    return {
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "authenticated_conversations": authenticated_conversations,
        "auth_rate": auth_rate,
        "messages_this_month": messages_this_month,
        "new_conversations_30d": new_conversations_30d,
        "whatsapp_count": whatsapp_count,
        "telegram_count": telegram_count,
    }


def get_conversations_by_channel_data():
    """
    Distribución de conversaciones por canal (WhatsApp vs Telegram).
    """
    try:
        from apps.chatbot.models import AgentConversation

        data = (
            AgentConversation.objects.values("channel")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        labels = []
        values = []
        for item in data:
            labels.append(item["channel"].title())
            values.append(item["count"])

        return {"labels": json.dumps(labels), "data": json.dumps(values)}
    except Exception:
        return {"labels": json.dumps([]), "data": json.dumps([])}


def get_conversations_by_status_data():
    """
    Distribución de conversaciones por estado.
    """
    try:
        from apps.chatbot.models import AgentConversation
        from apps.chatbot.choices import ConversationStatus

        data = (
            AgentConversation.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        labels = []
        values = []
        for item in data:
            try:
                label = str(ConversationStatus(item["status"]).label)
            except (ValueError, AttributeError):
                label = f"Status {item['status']}"
            labels.append(label)
            values.append(item["count"])

        return {"labels": json.dumps(labels), "data": json.dumps(values)}
    except Exception:
        return {"labels": json.dumps([]), "data": json.dumps([])}


def get_messages_by_intent_data():
    """
    Distribución de mensajes de usuarios por intent detectado.
    """
    try:
        from apps.chatbot.models import ConversationMessage
        from apps.chatbot.choices import IntentType, MessageSender

        data = (
            ConversationMessage.objects.filter(
                sender=MessageSender.USER,
                intent__isnull=False,
            )
            .exclude(intent="")
            .values("intent")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        labels = []
        values = []
        for item in data:
            try:
                label = str(IntentType(item["intent"]).label)
            except (ValueError, AttributeError):
                label = item["intent"].replace("_", " ").title()
            labels.append(label)
            values.append(item["count"])

        return {"labels": json.dumps(labels), "data": json.dumps(values)}
    except Exception:
        return {"labels": json.dumps([]), "data": json.dumps([])}


def get_messages_timeline_data(days=14):
    """
    Mensajes enviados por día en los últimos N días.
    """
    try:
        from apps.chatbot.models import ConversationMessage
        from apps.chatbot.choices import MessageSender

        today = timezone.now().date()
        start_date = today - timedelta(days=days - 1)

        messages = (
            ConversationMessage.objects.filter(
                created__date__gte=start_date,
                created__date__lte=today,
                sender=MessageSender.USER,
            )
            .annotate(date=TruncDate("created"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        date_counts = {start_date + timedelta(days=i): 0 for i in range(days)}
        for item in messages:
            date_counts[item["date"]] = item["count"]

        sorted_dates = sorted(date_counts.items())
        labels = [d.strftime("%d/%m") for d, _ in sorted_dates]
        values = [c for _, c in sorted_dates]

        return {"labels": json.dumps(labels), "data": json.dumps(values)}
    except Exception:
        today = timezone.now().date()
        labels = [
            (today - timedelta(days=i)).strftime("%d/%m")
            for i in range(days - 1, -1, -1)
        ]
        return {"labels": json.dumps(labels), "data": json.dumps([0] * days)}


def get_recent_conversations(limit=10):
    """
    Últimas N conversaciones con datos para la tabla del dashboard.
    """
    try:
        from apps.chatbot.models import AgentConversation
        from apps.chatbot.choices import ConversationStatus

        conversations = (
            AgentConversation.objects.select_related("partner")
            .annotate(message_count=Count("messages"))
            .order_by("-last_interaction")[:limit]
        )

        result = []
        for conv in conversations:
            result.append(
                {
                    "id": conv.id,
                    "identifier": conv.whatsapp_phone or conv.telegram_username or conv.telegram_chat_id or "—",
                    "channel": conv.channel,
                    "partner_name": conv.partner.full_name if conv.partner else "—",
                    "status": conv.status,
                    "status_label": str(ConversationStatus(conv.status).label),
                    "authenticated": conv.authenticated,
                    "message_count": conv.message_count,
                    "last_interaction": conv.last_interaction,
                }
            )
        return result
    except Exception:
        return []
