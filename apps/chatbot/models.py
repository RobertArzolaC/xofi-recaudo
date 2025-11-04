from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.chatbot import choices
from apps.core import models as core_models


class AgentConversation(core_models.BaseUserTracked, TimeStampedModel):
    """
    Model to track AI agent conversations with partners via Telegram.
    """

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.CASCADE,
        related_name="agent_conversations",
        null=True,
        blank=True,
        help_text=_("Partner associated with this conversation"),
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Telegram chat ID for this conversation"),
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Telegram username of the user"),
    )
    status = models.IntegerField(
        choices=choices.ConversationStatus.choices,
        default=choices.ConversationStatus.PENDING_AUTH,
        help_text=_("Current status of the conversation"),
    )
    authenticated = models.BooleanField(
        default=False,
        help_text=_("Whether the user has been authenticated"),
    )
    last_interaction = models.DateTimeField(
        auto_now=True,
        help_text=_("Last interaction timestamp"),
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Context data for the conversation (pending actions, state, etc.)"),
    )

    class Meta:
        verbose_name = _("Agent Conversation")
        verbose_name_plural = _("Agent Conversations")
        ordering = ["-last_interaction"]

    def __str__(self):
        if self.partner:
            return f"Conversation with {self.partner.full_name} ({self.telegram_chat_id})"
        return f"Conversation {self.telegram_chat_id}"


class ConversationMessage(TimeStampedModel):
    """
    Model to store messages in a conversation.
    """

    conversation = models.ForeignKey(
        AgentConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text=_("Conversation this message belongs to"),
    )
    sender = models.CharField(
        max_length=10,
        choices=choices.MessageSender.choices,
        help_text=_("Who sent this message"),
    )
    message = models.TextField(
        help_text=_("Message content"),
    )
    intent = models.CharField(
        max_length=50,
        choices=choices.IntentType.choices,
        blank=True,
        help_text=_("Detected intent of the message"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (API responses, file info, etc.)"),
    )

    class Meta:
        verbose_name = _("Conversation Message")
        verbose_name_plural = _("Conversation Messages")
        ordering = ["created"]

    def __str__(self):
        return f"{self.sender} - {self.message[:50]}"
