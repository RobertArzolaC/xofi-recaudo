import logging
from typing import Dict, Optional

from asgiref.sync import sync_to_async
from django.db import transaction

from apps.chatbot import choices, constants, models
from apps.chatbot.conversation import IntentDetector, MessageFormatter
from apps.chatbot.services.authentication import (
    PartnerAuthenticationService,
)
from apps.chatbot.services.partner_api import PartnerAPIService

logger = logging.getLogger(__name__)


class ConversationService:
    """Service to manage conversations with partners."""

    def __init__(self):
        """Initialize services."""
        self.intent_detector = IntentDetector()
        self.formatter = MessageFormatter()
        self.auth_service = PartnerAuthenticationService()
        self.api_service = PartnerAPIService()

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

    @sync_to_async
    @transaction.atomic
    def aget_or_create_conversation(
        self, telegram_chat_id: str, telegram_username: str = ""
    ) -> models.AgentConversation:
        """Async version: Get or create a conversation for a Telegram chat."""
        return self.get_or_create_conversation(
            telegram_chat_id, telegram_username
        )

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

    @sync_to_async
    @transaction.atomic
    def aget_or_create_conversation_whatsapp(
        self, whatsapp_phone: str
    ) -> models.AgentConversation:
        """Async version: Get or create a conversation for a WhatsApp phone number."""
        return self.get_or_create_conversation_whatsapp(whatsapp_phone)

    @transaction.atomic
    def save_message(
        self,
        conversation: models.AgentConversation,
        sender: str,
        message: str,
        intent: str = "",
        metadata: Optional[Dict] = None,
    ) -> models.ConversationMessage:
        """Save a message to the conversation."""
        return models.ConversationMessage.objects.create(
            conversation=conversation,
            sender=sender,
            message=message,
            intent=intent,
            metadata=metadata or {},
        )

    @sync_to_async
    @transaction.atomic
    def asave_message(
        self,
        conversation: models.AgentConversation,
        sender: str,
        message: str,
        intent: str = "",
        metadata: Optional[Dict] = None,
    ) -> models.ConversationMessage:
        """Async version: Save a message to the conversation."""
        return self.save_message(
            conversation, sender, message, intent, metadata
        )

    def process_message(
        self,
        telegram_chat_id: str,
        user_message: str,
        telegram_username: str = "",
    ) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            telegram_chat_id: Telegram chat ID
            user_message: User's message text
            telegram_username: Telegram username

        Returns:
            Agent's response text
        """
        # Get or create conversation
        conversation = self.get_or_create_conversation(
            telegram_chat_id, telegram_username
        )

        # Save user message
        self.save_message(
            conversation, choices.MessageSender.USER, user_message
        )

        # Check if authenticated
        if not conversation.authenticated:
            return self._handle_authentication(conversation, user_message)

        # Check if there's a pending action in context - priority over intent detection
        context = conversation.context_data
        pending_action = context.get("pending_action")

        if pending_action:
            # Route directly to the pending action handler without intent detection
            logger.info(
                f"Continuing pending action: {pending_action} for conversation {conversation.id}"
            )

            # Map pending actions to their corresponding intents
            pending_action_to_intent = {
                "create_ticket": choices.IntentType.CREATE_TICKET,
                "credit_detail": choices.IntentType.CREDIT_DETAIL,
            }

            intent = pending_action_to_intent.get(
                pending_action, choices.IntentType.UNKNOWN
            )
            response = self._route_intent(conversation, user_message, intent)

            # Save agent response
            self.save_message(
                conversation,
                choices.MessageSender.AGENT,
                response,
                intent=intent,
            )

            return response

        # Detect intent only if no pending action
        intent = self.intent_detector.detect_intent(user_message)
        logger.info(f"Detected intent: {intent} for message: {user_message}")

        # Route to appropriate handler
        response = self._route_intent(conversation, user_message, intent)

        # Save agent response
        self.save_message(
            conversation, choices.MessageSender.AGENT, response, intent=intent
        )

        return response

    async def aprocess_message(
        self,
        telegram_chat_id: str,
        user_message: str,
        telegram_username: str = "",
    ) -> str:
        """
        Async version: Process a user message and return the agent's response.

        Args:
            telegram_chat_id: Telegram chat ID
            user_message: User's message text
            telegram_username: Telegram username

        Returns:
            Agent's response text
        """
        # Get or create conversation
        conversation = await self.aget_or_create_conversation(
            telegram_chat_id, telegram_username
        )

        # Save user message
        await self.asave_message(
            conversation, choices.MessageSender.USER, user_message
        )

        # Check if authenticated
        if not conversation.authenticated:
            response = await self._ahandle_authentication(
                conversation, user_message
            )
            return response

        # Check if there's a pending action in context - priority over intent detection
        context = conversation.context_data
        pending_action = context.get("pending_action")

        if pending_action:
            # Route directly to the pending action handler without intent detection
            logger.info(
                f"Continuing pending action: {pending_action} for conversation {conversation.id}"
            )

            # Map pending actions to their corresponding intents
            pending_action_to_intent = {
                "create_ticket": choices.IntentType.CREATE_TICKET,
                "credit_detail": choices.IntentType.CREDIT_DETAIL,
            }

            intent = pending_action_to_intent.get(
                pending_action, choices.IntentType.UNKNOWN
            )
            response = await self._aroute_intent(
                conversation, user_message, intent
            )

            # Save agent response
            await self.asave_message(
                conversation,
                choices.MessageSender.AGENT,
                response,
                intent=intent,
            )

            return response

        # Detect intent only if no pending action
        intent = await sync_to_async(self.intent_detector.detect_intent)(
            user_message
        )
        logger.info(f"Detected intent: {intent} for message: {user_message}")

        # Route to appropriate handler
        response = await self._aroute_intent(conversation, user_message, intent)

        # Save agent response
        await self.asave_message(
            conversation, choices.MessageSender.AGENT, response, intent=intent
        )

        return response

    def _handle_authentication(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle authentication flow."""
        # Check if message contains auth data
        auth_data = self.intent_detector.extract_auth_data(message)

        if not auth_data:
            return self.formatter.format_authentication_prompt()

        # Attempt authentication
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
        else:
            return self.formatter.format_error_message(
                constants.AUTHENTICATION_ERROR
            )

    @sync_to_async
    def _ahandle_authentication(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Async version: Handle authentication flow."""
        return self._handle_authentication(conversation, message)

    def _route_intent(
        self, conversation: models.AgentConversation, message: str, intent: str
    ) -> str:
        """Route message to appropriate handler based on intent."""
        handlers = {
            choices.IntentType.AUTHENTICATION: self._handle_greeting,
            choices.IntentType.GREETING: self._handle_greeting,
            choices.IntentType.HELP: self._handle_help,
            choices.IntentType.PARTNER_DETAIL: self._handle_partner_detail,
            choices.IntentType.ACCOUNT_STATEMENT: self._handle_account_statement,
            choices.IntentType.LIST_CREDITS: self._handle_list_credits,
            choices.IntentType.CREDIT_DETAIL: self._handle_credit_detail,
            choices.IntentType.CREATE_TICKET: self._handle_create_ticket,
            choices.IntentType.UPLOAD_RECEIPT: self._handle_upload_receipt,
            choices.IntentType.GOODBYE: self._handle_goodbye,
        }

        handler = handlers.get(intent, self._handle_unknown)
        return handler(conversation, message)

    @sync_to_async
    def _aroute_intent(
        self, conversation: models.AgentConversation, message: str, intent: str
    ) -> str:
        """Async version: Route message to appropriate handler based on intent."""
        return self._route_intent(conversation, message, intent)

    def _handle_greeting(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle greeting messages."""
        partner_name = (
            conversation.partner.first_name
            if conversation.partner
            else "usuario"
        )
        return constants.GREETING_TEMPLATE.format(
            name=partner_name, menu=self.formatter.format_help_message()
        )

    def _handle_help(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle help requests."""
        return self.formatter.format_help_message()

    def _handle_partner_detail(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle partner detail requests."""
        if not conversation.partner:
            return self.formatter.format_error_message(
                constants.NO_PARTNER_INFO_ERROR
            )

        partner_data = {
            "full_name": conversation.partner.full_name,
            "document_number": conversation.partner.document_number,
            "phone": conversation.partner.phone or "N/A",
            "email": conversation.partner.email or "N/A",
        }
        return self.formatter.format_partner_info(partner_data)

    def _handle_account_statement(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle account statement requests."""
        if not conversation.partner:
            return self.formatter.format_error_message(
                constants.NO_PARTNER_INFO_ERROR
            )

        data = self.api_service.get_account_statement(conversation.partner.id)
        if not data:
            return self.formatter.format_error_message(
                constants.ACCOUNT_STATEMENT_ERROR
            )

        return self.formatter.format_account_statement(data)

    def _handle_list_credits(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle list credits requests."""
        if not conversation.partner:
            return self.formatter.format_error_message(
                constants.NO_PARTNER_INFO_ERROR
            )

        data = self.api_service.get_credits_list(conversation.partner.id)
        if not data:
            return self.formatter.format_error_message(
                constants.CREDITS_LIST_ERROR
            )

        credits = data.get("credits", [])
        return self.formatter.format_credits_list(credits)

    def _handle_credit_detail(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle credit detail requests."""
        if not conversation.partner:
            return self.formatter.format_error_message(
                constants.NO_PARTNER_INFO_ERROR
            )

        # Extract credit ID from message
        credit_id = self.intent_detector.extract_credit_id(message)
        if not credit_id:
            # Store context and ask for credit ID
            conversation.context_data["pending_action"] = "credit_detail"
            conversation.save()
            return constants.CREDIT_DETAIL_REQUEST

        data = self.api_service.get_credit_detail(
            conversation.partner.id, credit_id
        )
        if not data:
            return self.formatter.format_error_message(
                constants.CREDIT_DETAIL_ERROR
            )

        # Clear context
        conversation.context_data.pop("pending_action", None)
        conversation.save()

        return self.formatter.format_credit_detail(data)

    def _handle_create_ticket(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle support ticket creation."""
        if not conversation.partner:
            return self.formatter.format_error_message(
                constants.NO_PARTNER_INFO_ERROR
            )

        # Check if we have pending ticket data in context
        context = conversation.context_data
        if context.get("pending_action") != "create_ticket":
            conversation.context_data = {
                "pending_action": "create_ticket",
                "step": "subject",
            }
            conversation.save()
            return constants.TICKET_START_MESSAGE

        # Continue ticket creation flow
        step = context.get("step")
        if step == "subject":
            context["ticket_subject"] = message
            context["step"] = "description"
            conversation.context_data = context
            conversation.save()
            return constants.TICKET_DESCRIPTION_PROMPT

        elif step == "description":
            subject = context.get("ticket_subject", "Consulta desde chatbot")
            ticket_data = self.api_service.create_support_ticket(
                conversation.partner.document_number, subject, message
            )

            if ticket_data:
                # Clear context
                conversation.context_data = {}
                conversation.save()
                return self.formatter.format_success_message(
                    constants.TICKET_SUCCESS_TEMPLATE.format(
                        ticket_id=ticket_data.get("id")
                    )
                )
            else:
                return self.formatter.format_error_message(
                    constants.TICKET_ERROR
                )

        return self.formatter.format_error_message(constants.TICKET_FLOW_ERROR)

    def _handle_upload_receipt(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle payment receipt upload."""
        return constants.UPLOAD_RECEIPT_MESSAGE

    def _handle_goodbye(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle goodbye messages."""
        return constants.GOODBYE_MESSAGE

    def _handle_unknown(
        self, conversation: models.AgentConversation, message: str
    ) -> str:
        """Handle unknown intents."""
        try:
            logger.info(f"Wrong intent detected, for message: {message}")
            return self.formatter.format_help_message()
        except Exception as e:
            logger.error(f"Error handling unknown intent: {e}")
            return constants.UNKNOWN_INTENT_RESPONSE.format(
                menu=self.formatter.format_help_message()
            )

    async def aprocess_message_whatsapp(
        self,
        whatsapp_phone: str,
        user_message: str,
    ) -> str:
        """
        Async version: Process a user message from WhatsApp and return the agent's response.

        Args:
            whatsapp_phone: WhatsApp phone number
            user_message: User's message text

        Returns:
            Agent's response text
        """
        # Get or create conversation
        conversation = await self.aget_or_create_conversation_whatsapp(
            whatsapp_phone
        )

        # Save user message
        await self.asave_message(
            conversation, choices.MessageSender.USER, user_message
        )

        # Check if authenticated
        if not conversation.authenticated:
            response = await self._ahandle_authentication(
                conversation, user_message
            )
            return response

        # Check if there's a pending action in context - priority over intent detection
        context = conversation.context_data
        pending_action = context.get("pending_action")

        if pending_action:
            # Route directly to the pending action handler without intent detection
            logger.info(
                f"Continuing pending action: {pending_action} for conversation {conversation.id}"
            )

            # Map pending actions to their corresponding intents
            pending_action_to_intent = {
                "create_ticket": choices.IntentType.CREATE_TICKET,
                "credit_detail": choices.IntentType.CREDIT_DETAIL,
            }

            intent = pending_action_to_intent.get(
                pending_action, choices.IntentType.UNKNOWN
            )
            response = await self._aroute_intent(
                conversation, user_message, intent
            )

            # Save agent response
            await self.asave_message(
                conversation,
                choices.MessageSender.AGENT,
                response,
                intent=intent,
            )

            return response

        # Detect intent only if no pending action
        intent = await sync_to_async(self.intent_detector.detect_intent)(
            user_message
        )
        logger.info(f"Detected intent: {intent} for message: {user_message}")

        # Route to appropriate handler
        response = await self._aroute_intent(conversation, user_message, intent)

        # Save agent response
        await self.asave_message(
            conversation, choices.MessageSender.AGENT, response, intent=intent
        )

        return response
