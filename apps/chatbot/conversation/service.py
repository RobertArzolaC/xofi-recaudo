import datetime
import logging
from typing import Optional, Tuple

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.chatbot import choices, constants, models
from apps.chatbot.agent import AgentService
from apps.chatbot.conversation.message_formatter import MessageFormatter
from apps.chatbot.services.authentication import PartnerAuthenticationService

logger = logging.getLogger(__name__)


class ConversationService:
    """Service to manage conversations with partners."""

    def __init__(self):
        self.formatter = MessageFormatter()
        self.auth_service = PartnerAuthenticationService()
        self.agent_service = AgentService()

    # ------------------------------------------------------------------
    # Conversation retrieval
    # ------------------------------------------------------------------

    @transaction.atomic
    def get_or_create_conversation(
        self, telegram_chat_id: str, telegram_username: str = ""
    ) -> models.AgentConversation:
        """Get or create a conversation for a Telegram chat."""
        conversation, created = models.AgentConversation.objects.select_related(
            "partner"
        ).get_or_create(
            telegram_chat_id=telegram_chat_id,
            defaults={
                "telegram_username": telegram_username,
                "channel": choices.ChannelType.TELEGRAM,
            },
        )
        if created:
            logger.info(f"Created new conversation for chat {telegram_chat_id}")
        return conversation

    @transaction.atomic
    def get_or_create_conversation_whatsapp(
        self, whatsapp_phone: str
    ) -> models.AgentConversation:
        """Get or create a conversation for a WhatsApp phone number."""
        conversation, created = models.AgentConversation.objects.select_related(
            "partner"
        ).get_or_create(
            whatsapp_phone=whatsapp_phone,
            defaults={"channel": choices.ChannelType.WHATSAPP},
        )
        if created:
            logger.info(
                f"Created new conversation for WhatsApp {whatsapp_phone}"
            )
        return conversation

    @transaction.atomic
    def get_or_create_conversation_web(
        self, web_session_id: str
    ) -> models.AgentConversation:
        """Get or create a conversation for a Web session (testing)."""
        conversation, created = models.AgentConversation.objects.select_related(
            "partner"
        ).get_or_create(
            web_session_id=web_session_id,
            defaults={"channel": choices.ChannelType.WEB},
        )
        if created:
            logger.info(
                f"Created new conversation for Web session {web_session_id}"
            )
        return conversation

    # ------------------------------------------------------------------
    # Message persistence
    # ------------------------------------------------------------------

    @transaction.atomic
    def save_message(
        self,
        conversation: models.AgentConversation,
        sender: str,
        message: str,
        intent: str = "",
        metadata: Optional[dict] = None,
        whatsapp_message_id: Optional[str] = None,
        delivery_status: Optional[str] = None,
    ) -> models.ConversationMessage:
        """Save a message to the conversation."""
        msg = models.ConversationMessage.objects.create(
            conversation=conversation,
            sender=sender,
            message=message,
            intent=intent,
            metadata=metadata or {},
            whatsapp_message_id=whatsapp_message_id,
            delivery_status=delivery_status,
        )
        # Update last interaction timestamp
        conversation.save()
        return msg

    @sync_to_async
    def aget_or_create_conversation(
        self, telegram_chat_id: str, telegram_username: str = ""
    ) -> models.AgentConversation:
        """Async: Get or create a conversation for a Telegram chat."""
        return self.get_or_create_conversation(telegram_chat_id, telegram_username)

    @sync_to_async
    def asave_message(
        self,
        conversation: models.AgentConversation,
        sender: str,
        message: str,
        intent: str = "",
        metadata: Optional[dict] = None,
        whatsapp_message_id: Optional[str] = None,
        delivery_status: Optional[str] = None,
    ) -> models.ConversationMessage:
        """Async: Save a message to the conversation."""
        return self.save_message(
            conversation, sender, message, intent, metadata,
            whatsapp_message_id=whatsapp_message_id,
            delivery_status=delivery_status,
        )

    # ------------------------------------------------------------------
    # Message processing — Telegram
    # ------------------------------------------------------------------

    def process_message(
        self,
        telegram_chat_id: str,
        user_message: str,
        telegram_username: str = "",
    ) -> str:
        """Process a user message (Telegram) and return the agent's response."""
        conversation = self.get_or_create_conversation(
            telegram_chat_id, telegram_username
        )
        self._check_session_timeout(conversation)
        
        self.save_message(
            conversation, choices.MessageSender.USER, user_message
        )

        if not conversation.authenticated:
            return self._handle_authentication(conversation, user_message)

        response_text, tools_called = self.agent_service.process(
            conversation, user_message
        )

        tool_name = tools_called[0]["tool"] if tools_called else ""
        metadata = {"tools_called": tools_called} if tools_called else {}

        self.save_message(
            conversation,
            choices.MessageSender.AGENT,
            response_text,
            intent=tool_name,
            metadata=metadata,
        )
        return response_text

    @sync_to_async
    def aprocess_message(
        self,
        telegram_chat_id: str,
        user_message: str,
        telegram_username: str = "",
    ) -> str:
        """Async: Process a user message (Telegram)."""
        return self.process_message(telegram_chat_id, user_message, telegram_username)

    # ------------------------------------------------------------------
    # Message processing — WhatsApp
    # ------------------------------------------------------------------

    def process_message_whatsapp(
        self,
        whatsapp_phone: str,
        user_message: str,
    ) -> Tuple[str, None]:
        """
        Process a user message (WhatsApp) and return the agent's response.

        Returns:
            Tuple of (response_text, None). The second element is kept for
            backwards-compatibility with callers that expect an image_url slot.
        """
        conversation = self.get_or_create_conversation_whatsapp(whatsapp_phone)
        self._check_session_timeout(conversation)

        self.save_message(
            conversation, choices.MessageSender.USER, user_message
        )

        if not conversation.authenticated:
            response = self._handle_authentication(conversation, user_message)
            return response, None

        response_text, tools_called = self.agent_service.process(
            conversation, user_message
        )

        tool_name = tools_called[0]["tool"] if tools_called else ""
        metadata = {"tools_called": tools_called} if tools_called else {}

        self.save_message(
            conversation,
            choices.MessageSender.AGENT,
            response_text,
            intent=tool_name,
            metadata=metadata,
        )
        return response_text, None

    # ------------------------------------------------------------------
    # Message processing — Web (Testing)
    # ------------------------------------------------------------------

    def process_message_web(
        self,
        web_session_id: str,
        user_message: str,
    ) -> Tuple[str, list]:
        """
        Process a user message (Web) and return the agent's response.
        """
        conversation = self.get_or_create_conversation_web(web_session_id)
        self._check_session_timeout(conversation)

        self.save_message(
            conversation, choices.MessageSender.USER, user_message
        )

        if not conversation.authenticated:
            response = self._handle_authentication(conversation, user_message)
            return response, []

        response_text, tools_called = self.agent_service.process(
            conversation, user_message
        )

        tool_name = tools_called[0]["tool"] if tools_called else ""
        metadata = {"tools_called": tools_called} if tools_called else {}

        self.save_message(
            conversation,
            choices.MessageSender.AGENT,
            response_text,
            intent=tool_name,
            metadata=metadata,
        )
        return response_text, tools_called

    # ------------------------------------------------------------------
    # Authentication flow
    # ------------------------------------------------------------------

    def _handle_authentication(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle authentication flow."""
        auth_data = self.auth_service.extract_auth_data(message)

        if not auth_data:
            return self.formatter.format_authentication_prompt()

        partner = self.auth_service.authenticate(
            auth_data["document_number"], auth_data["birth_year"]
        )

        if partner:
            conversation.partner = partner
            conversation.authenticated = True
            conversation.status = choices.ConversationStatus.AUTHENTICATED
            conversation.save()

            logger.info(
                f"Partner {partner.id} authenticated in conversation {conversation.id}"
            )

            return self.formatter.format_success_message(
                constants.AUTHENTICATION_SUCCESS_TEMPLATE.format(
                    name=partner.full_name,
                    menu=self.formatter.format_help_message(),
                )
            )

        return self.formatter.format_error_message(
            constants.AUTHENTICATION_ERROR
        )

    def _check_session_timeout(self, conversation: models.AgentConversation) -> None:
        """Check if the session has expired and reset it if necessary."""
        if not conversation.authenticated:
            return

        timeout_minutes = getattr(settings, "CHATBOT_SESSION_TIMEOUT_MINUTES", 10)
        
        if timezone.now() - conversation.last_interaction > datetime.timedelta(minutes=timeout_minutes):
            logger.info(f"Conversation {conversation.id} timed out due to inactivity. Resetting.")
            conversation.partner = None
            conversation.authenticated = False
            conversation.status = choices.ConversationStatus.PENDING_AUTH
            conversation.context_data = {}
            conversation.save()
