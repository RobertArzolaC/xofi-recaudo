import logging

from decouple import config
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import (
    BooleanField,
    Case,
    Count,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.chatbot.choices import (
    ChannelType,
    ConversationStatus,
    MessageSender,
)
from apps.chatbot.models import AgentConversation, ConversationMessage
from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient
from apps.core.mixins import CacheMixin
from apps.dashboard import services

logger = logging.getLogger(__name__)


class DashboardView(CacheMixin, TemplateView):
    template_name = "dashboard/index.html"
    cache_timeout = 300

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Obtener KPIs principales
        kpis = services.get_dashboard_kpis()

        # Obtener datos para gráficos de campañas
        campaigns_by_status = services.get_campaigns_by_status_data()
        campaigns_by_channel = services.get_campaigns_by_channel_data()

        # Obtener datos para gráficos de pagos
        payments_by_method = services.get_payments_by_method_data()
        payments_timeline = services.get_payments_timeline_data()

        # Obtener datos para gráficos de créditos
        credits_by_status = services.get_credits_by_status_data()
        credits_outstanding_trend = (
            services.get_credits_outstanding_trend_data()
        )

        # Obtener datos para gráficos de socios
        partners_by_type = services.get_partners_by_type_data()
        partners_activity = services.get_partners_activity_data()

        # Obtener datos para gráficos de soporte
        tickets_by_status = services.get_tickets_by_status_data()
        tickets_timeline = services.get_tickets_timeline_data()

        context.update(
            {
                "last_updated": today,
                # KPIs principales
                "active_campaigns_count": kpis["active_campaigns_count"],
                "completed_campaigns_count": kpis["completed_campaigns_count"],
                "completed_payments_count": kpis["completed_payments_count"],
                "active_credits_count": kpis["active_credits_count"],
                "open_tickets_count": kpis["open_tickets_count"],
                "total_collected": kpis["total_collected"],
                "collection_rate": kpis["collection_rate"],
                # Datos de campañas
                "campaigns_by_status_labels": campaigns_by_status["labels"],
                "campaigns_by_status_data": campaigns_by_status["data"],
                "campaigns_by_channel_labels": campaigns_by_channel["labels"],
                "campaigns_by_channel_data": campaigns_by_channel["data"],
                # Datos de pagos
                "payments_by_method_labels": payments_by_method["labels"],
                "payments_by_method_data": payments_by_method["data"],
                "payments_timeline_labels": payments_timeline["labels"],
                "payments_timeline_data": payments_timeline["data"],
                # Datos de créditos
                "credits_by_status_labels": credits_by_status["labels"],
                "credits_by_status_data": credits_by_status["data"],
                "credits_outstanding_trend_labels": credits_outstanding_trend[
                    "labels"
                ],
                "credits_outstanding_trend_data": credits_outstanding_trend[
                    "data"
                ],
                # Datos de socios
                "partners_by_type_labels": partners_by_type["labels"],
                "partners_by_type_data": partners_by_type["data"],
                "partners_activity_labels": partners_activity["labels"],
                "partners_activity_data": partners_activity["data"],
                # Datos de soporte
                "tickets_by_status_labels": tickets_by_status["labels"],
                "tickets_by_status_data": tickets_by_status["data"],
                "tickets_timeline_labels": tickets_timeline["labels"],
                "tickets_timeline_data": tickets_timeline["data"],
            }
        )

        return context


TEMPLATE_CATEGORIES = [
    ("MARKETING", _("Marketing")),
    ("UTILITY", _("Utility")),
    ("AUTHENTICATION", _("Authentication")),
]

TEMPLATE_LANGUAGES = [
    ("es", _("Spanish")),
    ("es_PE", _("Spanish (Peru)")),
    ("es_MX", _("Spanish (Mexico)")),
    ("es_AR", _("Spanish (Argentina)")),
    ("en_US", _("English (US)")),
    ("pt_BR", _("Portuguese (Brazil)")),
]


class AdminChatbotTemplatesView(LoginRequiredMixin, TemplateView):
    template_name = "chatbot/admin/whatsapp_templates.html"

    def _get_client_and_waba(self):
        client = WhatsAppCloudAPIClient()
        waba_id = config("WHATSAPP_CLOUD_WABA_ID", default="")
        return client, waba_id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = TEMPLATE_CATEGORIES
        context["languages"] = TEMPLATE_LANGUAGES

        client, waba_id = self._get_client_and_waba()

        if not waba_id:
            context["api_error"] = _(
                "WHATSAPP_CLOUD_WABA_ID is not configured. "
                "Set it in your environment variables."
            )
            return context

        try:
            templates = client.list_templates(waba_id)
            context["templates"] = templates
            context["approved_count"] = sum(
                1 for t in templates if t.get("status") == "APPROVED"
            )
            context["pending_count"] = sum(
                1 for t in templates if t.get("status") == "PENDING"
            )
            context["rejected_count"] = sum(
                1 for t in templates if t.get("status") == "REJECTED"
            )
        except Exception as e:
            logger.error("Error fetching WhatsApp templates: %s", e)
            context["api_error"] = str(e)

        return context

    def post(self, request, *args, **kwargs):
        client, waba_id = self._get_client_and_waba()

        if not waba_id:
            messages.error(request, _("WHATSAPP_CLOUD_WABA_ID is not configured."))
            return redirect("apps.dashboard:admin_chatbot_templates")

        name = request.POST.get("name", "").strip().lower().replace(" ", "_")
        category = request.POST.get("category", "UTILITY")
        language = request.POST.get("language", "es")
        body_text = request.POST.get("body_text", "").strip()
        header_text = request.POST.get("header_text", "").strip()
        footer_text = request.POST.get("footer_text", "").strip()

        if not name or not body_text:
            messages.error(request, _("Template name and body text are required."))
            return redirect("apps.dashboard:admin_chatbot_templates")

        try:
            client.create_template(
                waba_id=waba_id,
                name=name,
                category=category,
                language=language,
                body_text=body_text,
                header_text=header_text,
                footer_text=footer_text,
            )
            messages.success(
                request,
                _("Template '%(name)s' submitted to Meta for review.") % {"name": name},
            )
        except Exception as e:
            logger.error("Error creating WhatsApp template: %s", e)
            messages.error(
                request,
                _("Error creating template: %(error)s") % {"error": str(e)},
            )

        return redirect("apps.dashboard:admin_chatbot_templates")


class AdminChatbotSendTestTemplateView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        template_name = request.POST.get("template_name", "").strip()
        language = request.POST.get("language", "es").strip()
        test_phone = request.POST.get("test_phone", "").strip()

        if not template_name or not test_phone:
            messages.error(request, _("Template name and phone number are required."))
            return redirect("apps.dashboard:admin_chatbot_templates")

        try:
            client = WhatsAppCloudAPIClient()
            client.send_template(
                to=test_phone,
                template_name=template_name,
                language=language,
            )
            messages.success(
                request,
                _("Test template '%(name)s' sent to %(phone)s.")
                % {"name": template_name, "phone": test_phone},
            )
        except Exception as e:
            logger.error("Error sending test template: %s", e)
            messages.error(
                request,
                _("Error sending template: %(error)s") % {"error": str(e)},
            )

        return redirect("apps.dashboard:admin_chatbot_templates")


# ------------------------------------------------------------------ #
# Chatbot — Dashboard, Conversations                                  #
# ------------------------------------------------------------------ #

STATUS_CONTEXT = {
    "STATUS_PENDING_AUTH": ConversationStatus.PENDING_AUTH,
    "STATUS_AUTHENTICATED": ConversationStatus.AUTHENTICATED,
    "STATUS_ACTIVE": ConversationStatus.ACTIVE,
    "STATUS_CLOSED": ConversationStatus.CLOSED,
    "STATUS_BLOCKED": ConversationStatus.BLOCKED,
}


def _last_sender_subquery():
    return Subquery(
        ConversationMessage.objects.filter(
            conversation=OuterRef("pk")
        )
        .order_by("-created")
        .values("sender")[:1]
    )


class AdminChatbotDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "chatbot/admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.chatbot.services.dashboard import (
            get_chatbot_kpis,
            get_delivery_stats,
            get_recent_conversations,
        )

        kpis = get_chatbot_kpis()
        context.update(kpis)
        context["delivery"] = get_delivery_stats()
        context["recent_conversations"] = get_recent_conversations(limit=10)
        return context


class AdminChatbotConversationsView(LoginRequiredMixin, TemplateView):
    template_name = "chatbot/admin/conversations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(STATUS_CONTEXT)

        last_sender = _last_sender_subquery()

        qs = (
            AgentConversation.objects.select_related("partner")
            .annotate(
                message_count=Count("messages"),
                last_sender=last_sender,
                has_pending_reply=Case(
                    When(last_sender=MessageSender.USER, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            .order_by("-last_interaction")
        )

        q = self.request.GET.get("q", "")
        status = self.request.GET.get("status", "")
        channel = self.request.GET.get("channel", "")
        pending = self.request.GET.get("pending", "")

        if q:
            qs = qs.filter(
                Q(whatsapp_phone__icontains=q)
                | Q(telegram_username__icontains=q)
                | Q(telegram_chat_id__icontains=q)
                | Q(partner__first_name__icontains=q)
                | Q(partner__paternal_last_name__icontains=q)
            )
        if status:
            qs = qs.filter(status=int(status))
        if channel:
            qs = qs.filter(channel=channel)
        if pending == "1":
            qs = qs.filter(has_pending_reply=True)

        pending_count = (
            AgentConversation.objects.annotate(last_sender=last_sender)
            .filter(last_sender=MessageSender.USER)
            .count()
        )

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(self.request.GET.get("page", 1))

        context["conversations"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["is_paginated"] = page_obj.has_other_pages()
        context["search_query"] = q
        context["current_status"] = status
        context["current_channel"] = channel
        context["current_pending"] = pending
        context["pending_count"] = pending_count
        context["status_choices"] = ConversationStatus.choices
        context["channel_choices"] = ChannelType.choices
        return context


class AdminChatbotConversationDetailView(LoginRequiredMixin, TemplateView):
    template_name = "chatbot/admin/conversation_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(STATUS_CONTEXT)

        conversation = get_object_or_404(
            AgentConversation.objects.select_related("partner").annotate(
                message_count=Count("messages"),
            ),
            pk=kwargs["pk"],
        )
        context["conversation"] = conversation
        context["chat_messages"] = conversation.messages.all().order_by("created")
        return context


class AdminChatbotConversationsPendingStatusView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        pending_ids = list(
            AgentConversation.objects.annotate(
                last_sender=_last_sender_subquery()
            )
            .filter(last_sender=MessageSender.USER)
            .values_list("id", flat=True)
        )
        return JsonResponse({"pending_ids": pending_ids, "count": len(pending_ids)})
