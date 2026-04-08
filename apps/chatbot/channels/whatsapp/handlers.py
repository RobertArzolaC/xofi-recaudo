import logging

from constance import config
from django.conf import settings

from apps.chatbot import constants
from apps.chatbot.conversation import ConversationService
from apps.core.services.chats.whatsapp_official import WhatsAppOfficialService
from apps.core.utils.urls import get_absolute_url


logger = logging.getLogger(__name__)


class WhatsAppBotHandler:
    """
    Sync helper for WhatsApp management commands.

    Webhook processing has been migrated to the Celery task
    `chatbot.process_whatsapp_webhook` in apps/chatbot/tasks.py.
    """

    def __init__(self):
        self.conversation_service = ConversationService()
        self.whatsapp_service = WhatsAppOfficialService()

    def handle_start_command(self, sender_phone: str) -> None:
        """Send the welcome message (and image if configured)."""
        welcome_message = config.CHATBOT_WELCOME_MESSAGE
        welcome_image = config.CHATBOT_WELCOME_IMAGE

        if welcome_image:
            media_url = settings.MEDIA_URL.strip("/")
            image_url = get_absolute_url(f"/{media_url}/constance/{welcome_image}")
            self.whatsapp_service.send_image_message(sender_phone, image_url, welcome_message)
        else:
            self.whatsapp_service.send_text_message(sender_phone, welcome_message)

    def handle_help_command(self, sender_phone: str) -> None:
        """Send the help message."""
        self.whatsapp_service.send_text_message(sender_phone, constants.HELP_MESSAGE)

    def handle_menu_command(self, sender_phone: str) -> None:
        """Send the menu message."""
        response = self.conversation_service.formatter.format_help_message()
        self.whatsapp_service.send_text_message(sender_phone, response)
