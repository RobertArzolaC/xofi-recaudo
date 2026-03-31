import json
import logging

from constance import config
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from apps.chatbot import services as chatbot_services
from apps.chatbot.choices import TemplateStatus
from apps.chatbot.forms import ChatbotSettingsForm
from apps.chatbot.models import AgentConversation, ConversationMessage, WhatsAppTemplate
from apps.chatbot.tasks import process_whatsapp_webhook
from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient
from apps.core.clients.exceptions import APIClientError

logger = logging.getLogger(__name__)


class ChatbotDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard with chatbot analytics and conversation metrics."""

    template_name = "chatbot/dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kpis"] = chatbot_services.get_chatbot_kpis()
        context["channel_chart"] = (
            chatbot_services.get_conversations_by_channel_data()
        )
        context["status_chart"] = (
            chatbot_services.get_conversations_by_status_data()
        )
        context["intent_chart"] = chatbot_services.get_messages_by_intent_data()
        context["timeline_chart"] = (
            chatbot_services.get_messages_timeline_data()
        )
        context["recent_conversations"] = (
            chatbot_services.get_recent_conversations()
        )
        context["delivery_stats"] = chatbot_services.get_delivery_stats()
        context["templates"] = chatbot_services.get_templates()
        context["template_stats"] = chatbot_services.get_template_stats()
        return context


class ChatbotSettingsDetailView(LoginRequiredMixin, TemplateView):
    """View to display chatbot settings."""

    template_name = "chatbot/settings/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["welcome_image"] = config.CHATBOT_WELCOME_IMAGE
        context["welcome_message"] = config.CHATBOT_WELCOME_MESSAGE
        return context


class ChatbotSettingsUpdateView(LoginRequiredMixin, FormView):
    """View to update chatbot settings."""

    template_name = "chatbot/settings/form.html"
    form_class = ChatbotSettingsForm
    success_url = reverse_lazy("apps.chatbot:chatbot-settings-detail")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["welcome_image"] = config.CHATBOT_WELCOME_IMAGE
        context["action"] = _("Edit")
        return context

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request, _("Chatbot settings updated successfully.")
        )
        return super().form_valid(form)


class TemplateCreateView(LoginRequiredMixin, View):
    """
    Create a new WhatsApp template and immediately submit it to Meta for review.

    Flow:
    1. Validate + save to local DB (status=PENDING, no meta_template_id yet).
    2. Call Meta Graph API to create the template.
    3. On success → update meta_template_id with Meta's returned ID.
    4. On API failure → template stays in DB as PENDING so the user can retry.
    """

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip().lower().replace(" ", "_")
        category = request.POST.get("category", "UTILITY")
        language = request.POST.get("language", "es")
        body = request.POST.get("body", "").strip()

        if not name or not body:
            return JsonResponse(
                {"ok": False, "error": "Name and body are required."},
                status=400,
            )

        if WhatsAppTemplate.objects.filter(name=name).exists():
            return JsonResponse(
                {
                    "ok": False,
                    "error": "A template with that name already exists.",
                },
                status=400,
            )

        tpl = WhatsAppTemplate.objects.create(
            name=name,
            category=category,
            language=language,
            body=body,
            status=TemplateStatus.PENDING,
        )

        # Submit to Meta
        meta_id = None
        meta_error = None
        client = WhatsAppCloudAPIClient()

        if not client.waba_id:
            meta_error = "WHATSAPP_CLOUD_WABA_ID not configured — template saved locally only."
            logger.warning(meta_error)
        else:
            try:
                response = client.create_template(
                    waba_id=client.waba_id,
                    name=name,
                    category=category,
                    language=language,
                    body_text=body,
                )
                meta_id = response.get("id") or response.get("template_id")
                if meta_id:
                    tpl.meta_template_id = str(meta_id)
                    tpl.save(update_fields=["meta_template_id"])
                    logger.info(
                        "Template '%s' submitted to Meta, id=%s", name, meta_id
                    )
            except APIClientError as exc:
                meta_error = str(exc)
                logger.error(
                    "Meta API error creating template '%s': %s", name, exc
                )
            except Exception as exc:
                meta_error = str(exc)
                logger.error(
                    "Unexpected error submitting template '%s' to Meta: %s", name, exc
                )

        return JsonResponse(
            {
                "ok": True,
                "id": tpl.id,
                "name": tpl.name,
                "status": tpl.status,
                "meta_template_id": tpl.meta_template_id,
                "created": tpl.created.strftime("%d/%m/%Y"),
                "meta_submitted": meta_id is not None,
                "meta_error": meta_error,
            }
        )


class TemplateSyncView(LoginRequiredMixin, View):
    """
    Sync a template's approval status from Meta.

    If the template already has a meta_template_id → fetch its current status
    from Meta and update the local record.

    If not (e.g. first submission failed) → re-submit to Meta and save the ID.
    """

    def post(self, request, pk, *args, **kwargs):
        tpl = get_object_or_404(WhatsAppTemplate, pk=pk)
        client = WhatsAppCloudAPIClient()

        if not client.waba_id and not tpl.meta_template_id:
            return JsonResponse(
                {
                    "ok": False,
                    "error": "WHATSAPP_CLOUD_WABA_ID not configured.",
                },
                status=400,
            )

        try:
            if tpl.meta_template_id:
                # Template exists on Meta — fetch current status
                meta_data = client.get_template(tpl.meta_template_id)
                raw_status = meta_data.get("status", "").upper()
                status_map = {
                    "APPROVED": TemplateStatus.APPROVED,
                    "REJECTED": TemplateStatus.REJECTED,
                    "PAUSED": TemplateStatus.PAUSED,
                    "PENDING": TemplateStatus.PENDING,
                    "PENDING_DELETION": TemplateStatus.PAUSED,
                    "DISABLED": TemplateStatus.PAUSED,
                }
                new_status = status_map.get(raw_status, tpl.status)
                tpl.status = new_status
                tpl.save(update_fields=["status"])
                logger.info(
                    "Template '%s' synced from Meta: status=%s", tpl.name, new_status
                )
            else:
                # Never reached Meta — try to submit now
                if not client.waba_id:
                    return JsonResponse(
                        {"ok": False, "error": "WHATSAPP_CLOUD_WABA_ID not configured."},
                        status=400,
                    )
                response = client.create_template(
                    waba_id=client.waba_id,
                    name=tpl.name,
                    category=tpl.category,
                    language=tpl.language,
                    body_text=tpl.body,
                )
                meta_id = response.get("id") or response.get("template_id")
                if meta_id:
                    tpl.meta_template_id = str(meta_id)
                    tpl.save(update_fields=["meta_template_id"])

        except APIClientError as exc:
            logger.error("Meta API error syncing template %s: %s", pk, exc)
            return JsonResponse({"ok": False, "error": str(exc)}, status=502)
        except Exception as exc:
            logger.error("Unexpected error syncing template %s: %s", pk, exc)
            return JsonResponse({"ok": False, "error": str(exc)}, status=500)

        return JsonResponse(
            {
                "ok": True,
                "id": tpl.id,
                "status": tpl.status,
                "meta_template_id": tpl.meta_template_id,
            }
        )


class TemplateDeleteView(LoginRequiredMixin, View):
    """Delete a template locally and, if possible, from Meta as well."""

    def post(self, request, pk, *args, **kwargs):
        tpl = get_object_or_404(WhatsAppTemplate, pk=pk)
        client = WhatsAppCloudAPIClient()

        # Best-effort deletion from Meta
        if tpl.meta_template_id and client.waba_id:
            try:
                client.delete_template(name=tpl.name, waba_id=client.waba_id)
            except APIClientError as exc:
                logger.warning(
                    "Could not delete template '%s' from Meta: %s", tpl.name, exc
                )

        tpl.delete()
        return JsonResponse({"ok": True})


class ConversationHistoryView(LoginRequiredMixin, TemplateView):
    """Show the full message history for a single conversation."""

    template_name = "chatbot/conversation/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = get_object_or_404(
            AgentConversation.objects.select_related("partner"),
            pk=self.kwargs["pk"],
        )
        messages_qs = (
            ConversationMessage.objects.filter(conversation=conversation)
            .order_by("created")
        )
        context["conversation"] = conversation
        context["messages"] = messages_qs
        return context


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    """
    Webhook endpoint for Meta WhatsApp Business Cloud API.

    GET  → webhook verification (hub.challenge)
    POST → incoming messages, validated via HMAC-SHA256 signature;
        processing is delegated to the Celery task
        `chatbot.process_whatsapp_webhook` so Meta receives an
        immediate 200 response.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.whatsapp_client = WhatsAppCloudAPIClient()

    # ------------------------------------------------------------------ #
    # GET — Meta webhook verification                                      #
    # ------------------------------------------------------------------ #
    def get(self, request, *args, **kwargs):
        """
        Meta sends a GET with three query params when you register the webhook:
        hub.mode         = "subscribe"
        hub.verify_token = <the token you set in Meta dashboard>
        hub.challenge    = <random string Meta wants echoed back>
        """
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        result = self.whatsapp_client.verify_webhook_challenge(
            mode, token, challenge
        )
        if result is not None:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(result, content_type="text/plain", status=200)

        logger.warning(
            "Webhook verification failed — mode=%s, token_match=%s",
            mode,
            token == self.whatsapp_client.verify_token,
        )
        return HttpResponse("Forbidden", status=403)

    # ------------------------------------------------------------------ #
    # POST — incoming events                                               #
    # ------------------------------------------------------------------ #
    def post(self, request, *args, **kwargs):
        """
        Meta signs every POST with X-Hub-Signature-256: sha256=<hex>.
        We verify the signature before dispatching the Celery task.
        """
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        if not self.whatsapp_client.verify_webhook_signature(
            request.body, signature_header
        ):
            logger.warning(
                "WhatsApp webhook signature mismatch — request rejected"
            )
            return HttpResponse("Forbidden", status=403)

        try:
            body = json.loads(request.body)
            logger.info("Received webhook, dispatching to Celery")
            process_whatsapp_webhook.delay(body)
            return JsonResponse({"status": "success"}, status=200)

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in webhook: %s", e)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
