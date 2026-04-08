import json
import logging

from constance import config
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from apps.chatbot import services as chatbot_services
from apps.chatbot.choices import TemplateStatus
from apps.chatbot.conversation import ConversationService
from apps.chatbot.forms import ChatbotSettingsForm
from apps.chatbot.models import WhatsAppTemplate
from apps.chatbot.tasks import process_whatsapp_webhook
from apps.core.clients.whatsapp_cloud import WhatsAppCloudAPIClient

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


class ChatbotSettingsDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    """View to display chatbot settings."""

    template_name = "chatbot/settings/detail.html"
    permission_required = "customers.view_chatbot_settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["welcome_image"] = config.CHATBOT_WELCOME_IMAGE
        context["welcome_message"] = config.CHATBOT_WELCOME_MESSAGE
        return context


class ChatbotSettingsUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    """View to update chatbot settings."""

    template_name = "chatbot/settings/form.html"
    form_class = ChatbotSettingsForm
    permission_required = "customers.change_chatbot_settings"
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
    """Create a new WhatsApp template (submitted to Meta for review)."""

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
        return JsonResponse(
            {
                "ok": True,
                "id": tpl.id,
                "name": tpl.name,
                "status": tpl.status,
                "created": tpl.created.strftime("%d/%m/%Y"),
            }
        )


class TemplateApproveView(LoginRequiredMixin, View):
    """Simulate Meta approval sync — marks a PENDING template as APPROVED."""

    def post(self, request, pk, *args, **kwargs):
        try:
            tpl = WhatsAppTemplate.objects.get(pk=pk)
        except WhatsAppTemplate.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": "Template not found."}, status=404
            )

        import secrets

        tpl.status = TemplateStatus.APPROVED
        tpl.meta_template_id = (
            tpl.meta_template_id or f"MT-{secrets.token_hex(4).upper()}"
        )
        tpl.save(update_fields=["status", "meta_template_id"])

        return JsonResponse(
            {
                "ok": True,
                "id": tpl.id,
                "status": tpl.status,
                "meta_template_id": tpl.meta_template_id,
            }
        )


class ChatbotTestView(LoginRequiredMixin, TemplateView):
    """View to test the chatbot agent in a web interface."""

    template_name = "chatbot/test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use a consistent session ID for the current user for testing
        session_id = f"test-user-{self.request.user.id}"
        conv_service = ConversationService()
        conversation = conv_service.get_or_create_conversation_web(session_id)

        context["session_id"] = session_id
        context["conversation"] = conversation
        context["messages"] = conversation.messages.all().order_by("created")
        return context

    def post(self, request, *args, **kwargs):
        """Handle incoming test messages via AJAX."""
        user_message = request.POST.get("message", "").strip()
        session_id = request.POST.get(
            "session_id", f"test-user-{request.user.id}"
        )

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        conv_service = ConversationService()

        try:
            response_text, tools_called = conv_service.process_message_web(
                session_id, user_message
            )
            return JsonResponse(
                {"response": response_text, "tools_called": tools_called}
            )
        except Exception as e:
            logger.error(f"Error in ChatbotTestView: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


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
