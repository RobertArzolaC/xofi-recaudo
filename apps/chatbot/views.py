import json
import logging

from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.chatbot.channels.whatsapp.handlers import WhatsAppBotHandler

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    """
    View to handle WhatsApp webhook callbacks.

    This view handles both webhook verification (GET) and incoming messages (POST).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.handler = WhatsAppBotHandler()

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests (webhook health check).

        WHAPI doesn't require webhook verification like Meta,
        so this just returns a simple OK response.
        """
        logger.info("Webhook health check request received")
        return JsonResponse({"status": "ok", "service": "whatsapp_chatbot"})

    def post(self, request, *args, **kwargs):
        """
        Handle incoming WhatsApp messages.

        WhatsApp sends POST requests with message data in JSON format.
        """
        try:
            # Parse webhook data
            body = json.loads(request.body)
            logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

            # Process webhook asynchronously
            # Use async_to_sync to handle async handler in sync view
            result = async_to_sync(self.handler.handle_webhook)(body)

            logger.info(f"Webhook processing result: {result}")

            # WhatsApp expects a 200 OK response
            return JsonResponse({"status": "success"}, status=200)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            # Still return 200 to avoid WhatsApp retries
            return JsonResponse(
                {"status": "error", "error": str(e)}, status=200
            )
