from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.chatbot import choices
from apps.core import models as core_models


class AgentConversation(core_models.BaseUserTracked, TimeStampedModel):
    """
    Model to track AI agent conversations with partners via Telegram or WhatsApp.
    """

    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.CASCADE,
        related_name="agent_conversations",
        null=True,
        blank=True,
        help_text=_("Partner associated with this conversation"),
    )
    channel = models.CharField(
        max_length=20,
        choices=choices.ChannelType.choices,
        default=choices.ChannelType.TELEGRAM,
        help_text=_("Communication channel (Telegram or WhatsApp)"),
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Telegram chat ID for this conversation"),
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Telegram username of the user"),
    )
    whatsapp_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_("WhatsApp phone number for this conversation"),
    )
    web_session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Web session ID for testing purposes"),
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
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(channel="TELEGRAM", telegram_chat_id__isnull=False)
                    | models.Q(channel="WHATSAPP", whatsapp_phone__isnull=False)
                    | models.Q(channel="WEB", web_session_id__isnull=False)
                ),
                name="channel_identifier_required",
            ),
            models.UniqueConstraint(
                fields=["telegram_chat_id"],
                condition=models.Q(telegram_chat_id__isnull=False),
                name="unique_telegram_chat_id",
            ),
            models.UniqueConstraint(
                fields=["whatsapp_phone"],
                condition=models.Q(whatsapp_phone__isnull=False),
                name="unique_whatsapp_phone",
            ),
            models.UniqueConstraint(
                fields=["web_session_id"],
                condition=models.Q(web_session_id__isnull=False),
                name="unique_web_session_id",
            ),
        ]

    def __str__(self):
        identifier = self.telegram_chat_id or self.whatsapp_phone or self.web_session_id
        if self.partner:
            return f"Conversation with {self.partner.full_name} ({identifier})"
        return f"Conversation {identifier}"


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
        max_length=100,
        blank=True,
        default="",
        help_text=_("Tool name called by the agent, if any"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (API responses, file info, etc.)"),
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=choices.MessageDeliveryStatus.choices,
        blank=True,
        null=True,
        help_text=_("Delivery status for outbound WhatsApp messages"),
    )
    whatsapp_message_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("WhatsApp message ID for delivery tracking"),
    )

    class Meta:
        verbose_name = _("Conversation Message")
        verbose_name_plural = _("Conversation Messages")
        ordering = ["created"]

    def __str__(self):
        return f"{self.sender} - {self.message[:50]}"


class WhatsAppTemplate(TimeStampedModel):
    """
    Model to track WhatsApp Message Templates and their Meta approval status.
    """

    name = models.CharField(
        max_length=100,
        help_text=_("Template name (as registered in Meta)"),
    )
    category = models.CharField(
        max_length=50,
        help_text=_("Template category (MARKETING, UTILITY, AUTHENTICATION)"),
    )
    language = models.CharField(
        max_length=10,
        default="es",
        help_text=_("Template language code"),
    )
    status = models.CharField(
        max_length=20,
        choices=choices.TemplateStatus.choices,
        default=choices.TemplateStatus.PENDING,
        help_text=_("Meta approval status"),
    )
    body = models.TextField(
        help_text=_("Template body text"),
    )
    meta_template_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Template ID assigned by Meta"),
    )
    times_used = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times this template has been sent"),
    )

    class Meta:
        verbose_name = _("WhatsApp Template")
        verbose_name_plural = _("WhatsApp Templates")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.status})"
