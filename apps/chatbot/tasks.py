import logging
from typing import Dict

from celery import shared_task

from apps.chatbot.services.webhook_processor import WhatsAppWebhookProcessor

logger = logging.getLogger(__name__)


@shared_task(
    name="chatbot.process_whatsapp_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_whatsapp_webhook(self, webhook_data: Dict) -> Dict:
    """
    Process an incoming Meta WhatsApp Business Cloud API webhook payload.

    Refactored to use WhatsAppWebhookProcessor for better structure and scalability.
    """
    try:
        processor = WhatsAppWebhookProcessor()
        return processor.process(webhook_data)

    except Exception as exc:
        logger.error("Error processing webhook task: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
