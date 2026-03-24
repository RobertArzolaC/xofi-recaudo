import hashlib
import hmac
import json
import logging

from asgiref.sync import async_to_sync
from constance import config
from django.conf import settings
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

from apps.chatbot.channels.whatsapp.handlers import WhatsAppBotHandler
from apps.chatbot.forms import ChatbotSettingsForm
from apps.chatbot import services as chatbot_services

logger = logging.getLogger(__name__)


class ChatbotDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard with chatbot analytics and conversation metrics."""

    template_name = "chatbot/dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kpis"] = chatbot_services.get_chatbot_kpis()
        context["channel_chart"] = chatbot_services.get_conversations_by_channel_data()
        context["status_chart"] = chatbot_services.get_conversations_by_status_data()
        context["intent_chart"] = chatbot_services.get_messages_by_intent_data()
        context["timeline_chart"] = chatbot_services.get_messages_timeline_data()
        context["recent_conversations"] = chatbot_services.get_recent_conversations()
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


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    """
    Webhook endpoint for Meta WhatsApp Business Cloud API.

    GET  → webhook verification (hub.challenge)
    POST → incoming messages, validated via HMAC-SHA256 signature
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.handler = WhatsAppBotHandler()

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

        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")

        if mode == "subscribe" and token == verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge, content_type="text/plain", status=200)

        logger.warning(
            f"Webhook verification failed — mode={mode}, token_match={token == verify_token}"
        )
        return HttpResponse("Forbidden", status=403)

    # ------------------------------------------------------------------ #
    # POST — incoming events                                               #
    # ------------------------------------------------------------------ #
    def post(self, request, *args, **kwargs):
        """
        Meta signs every POST with X-Hub-Signature-256: sha256=<hex>.
        We verify the signature before processing anything.
        """
        # 1. Validate signature
        if not self._verify_signature(request):
            logger.warning("WhatsApp webhook signature mismatch — request rejected")
            return HttpResponse("Forbidden", status=403)

        try:
            body = json.loads(request.body)
            logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

            result = async_to_sync(self.handler.handle_webhook)(body)
            logger.info(f"Webhook result: {result}")

            # Meta expects 200 quickly; errors are logged but we still return 200
            return JsonResponse({"status": "success"}, status=200)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return JsonResponse({"status": "error"}, status=200)

    # ------------------------------------------------------------------ #
    # Signature validation                                                 #
    # ------------------------------------------------------------------ #
    def _verify_signature(self, request) -> bool:
        """
        Verify X-Hub-Signature-256 header using WHATSAPP_APP_SECRET.
        Returns True if valid or if APP_SECRET is not configured (dev mode).
        """
        app_secret = getattr(settings, "WHATSAPP_APP_SECRET", "")
        if not app_secret:
            logger.warning("WHATSAPP_APP_SECRET not set — skipping signature verification")
            return True

        signature_header = request.headers.get("X-Hub-Signature-256", "")
        if not signature_header.startswith("sha256="):
            return False

        expected_signature = signature_header[len("sha256="):]
        computed = hmac.new(
            key=app_secret.encode("utf-8"),
            msg=request.body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, expected_signature)
