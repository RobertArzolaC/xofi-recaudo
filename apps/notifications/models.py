from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.notifications import choices


class CampaignNotification(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """
    Model to register notifications sent during campaign execution.

    Uses GenericForeignKey to support different campaign types
    (Campaign, CampaignCSVFile) and recipient types (Partner, CSVContact).
    """

    # Campaign reference (generic)
    campaign_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="campaign_notifications",
        limit_choices_to={"model__in": ("campaign", "campaigncsvfile")},
        verbose_name=_("Campaign Type"),
    )
    campaign_id = models.PositiveIntegerField(_("Campaign ID"))
    campaign = GenericForeignKey("campaign_type", "campaign_id")

    # Recipient reference (generic)
    recipient_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="notifications_as_recipient",
        limit_choices_to={"model__in": ("partner", "csvcontact")},
        verbose_name=_("Recipient Type"),
    )
    recipient_id = models.PositiveIntegerField(_("Recipient ID"))
    recipient = GenericForeignKey("recipient_type", "recipient_id")

    # Notification details
    notification_type = models.CharField(
        _("Notification Type"),
        max_length=20,
        choices=choices.NotificationType.choices,
        help_text=_(
            "Type of notification sent (before due date, on due date, etc.)."
        ),
    )
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=choices.NotificationChannel.choices,
        default=choices.NotificationChannel.WHATSAPP,
        help_text=_("Communication channel used for the notification."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.NotificationStatus.choices,
        default=choices.NotificationStatus.PENDING,
        help_text=_("Current status of the notification."),
    )

    # Contact information
    recipient_email = models.EmailField(
        _("Recipient Email"),
        null=True,
        blank=True,
        help_text=_("Email address where the notification was sent."),
    )
    recipient_phone = models.CharField(
        _("Recipient Phone"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Phone number where the notification was sent."),
    )
    recipient_telegram_id = models.CharField(
        _("Recipient Telegram ID"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Telegram ID where the notification was sent."),
    )

    # Message content
    message_content = models.TextField(
        _("Message Content"),
        null=True,
        blank=True,
        help_text=_("Content of the notification message."),
    )

    # Scheduling
    scheduled_at = models.DateTimeField(
        _("Scheduled At"),
        null=True,
        blank=True,
        help_text=_(
            "Date and time when the notification is scheduled to be sent."
        ),
    )
    sent_at = models.DateTimeField(
        _("Sent At"),
        null=True,
        blank=True,
        help_text=_("Date and time when the notification was actually sent."),
    )

    # Error handling
    error_message = models.TextField(
        _("Error Message"),
        null=True,
        blank=True,
        help_text=_("Error message if the notification failed to send."),
    )

    # Payment information
    total_debt_amount = models.DecimalField(
        _("Total Debt Amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(
            "Total debt amount for the partner at the time of notification."
        ),
    )
    included_payment_link = models.BooleanField(
        _("Included Payment Link"),
        default=False,
        help_text=_("Whether a payment link was included in the notification."),
    )
    payment_link_url = models.URLField(
        _("Payment Link URL"),
        null=True,
        blank=True,
        help_text=_("URL of the payment link included in the notification."),
    )

    # Tracking fields for notification attempts
    attempt_count = models.PositiveIntegerField(
        _("Attempt Count"),
        default=0,
        help_text=_("Number of attempts made to send this notification."),
    )
    last_attempt_at = models.DateTimeField(
        _("Last Attempt At"),
        null=True,
        blank=True,
        help_text=_(
            "Date and time of the last attempt to send the notification."
        ),
    )

    class Meta:
        verbose_name = _("Campaign Notification")
        verbose_name_plural = _("Campaign Notifications")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["campaign_type", "campaign_id"]),
            models.Index(fields=["recipient_type", "recipient_id"]),
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["channel", "status"]),
        ]

    def __str__(self):
        try:
            campaign_name = self.campaign.name if self.campaign else "Unknown"
            recipient_name = (
                getattr(self.recipient, "full_name", "Unknown")
                if self.recipient
                else "Unknown"
            )
            return (
                f"{campaign_name} - {recipient_name} - "
                f"{self.get_notification_type_display()} ({self.get_status_display()})"
            )
        except Exception:
            return f"Notification #{self.id}"

    @property
    def is_pending(self):
        """Check if notification is pending."""
        return self.status == choices.NotificationStatus.PENDING

    @property
    def is_sent(self):
        """Check if notification was sent successfully."""
        return self.status == choices.NotificationStatus.SENT

    @property
    def is_failed(self):
        """Check if notification failed to send."""
        return self.status == choices.NotificationStatus.FAILED

    def mark_as_sent(self):
        """Mark notification as sent and update sent_at timestamp."""
        self.status = choices.NotificationStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at"])

    def mark_as_failed(self, error_message=None):
        """Mark notification as failed and optionally store error message."""
        self.status = choices.NotificationStatus.FAILED
        if error_message:
            self.error_message = error_message
        self.save(update_fields=["status", "error_message"])

    def increment_attempt(self):
        """Increment the attempt count and update last attempt timestamp."""
        self.attempt_count += 1
        self.last_attempt_at = timezone.now()
        self.save(update_fields=["attempt_count", "last_attempt_at"])


class MessageTemplate(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """
    Model to store message templates for notifications.

    Templates can be used across different channels (WhatsApp, Telegram, Email, SMS)
    and can include placeholders for dynamic content.
    """

    template_type = models.CharField(
        _("Template Type"),
        max_length=20,
        choices=choices.NotificationType.choices,
        help_text=_("Type of notification this template is for."),
    )
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=choices.NotificationChannel.choices,
        default=choices.NotificationChannel.WHATSAPP,
        help_text=_("Communication channel for this template."),
    )
    subject = models.CharField(
        _("Subject"),
        max_length=200,
        null=True,
        blank=True,
        help_text=_("Subject line for email notifications (optional)."),
    )
    message_body = models.TextField(
        _("Message Body"),
        help_text=_(
            "Template body with placeholders: {partner_name}, {debt_amount}, "
            "{payment_link}, {due_date}, {company_name}, {contact_phone}"
        ),
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this template is currently active."),
    )

    # WhatsApp-specific fields
    whatsapp_template_name = models.CharField(
        _("WhatsApp Template Name"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_(
            "Name of the approved WhatsApp Business template (if using templates)."
        ),
    )
    include_payment_button = models.BooleanField(
        _("Include Payment Button"),
        default=False,
        help_text=_("Whether to include a payment button/link in the message."),
    )
    payment_button_text = models.CharField(
        _("Payment Button Text"),
        max_length=50,
        default="Pagar ahora",
        help_text=_("Text to display on the payment button/link."),
    )

    class Meta:
        verbose_name = _("Message Template")
        verbose_name_plural = _("Message Templates")
        ordering = ["-created"]
        unique_together = [("template_type", "channel", "is_active")]
        indexes = [
            models.Index(fields=["template_type", "channel", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()} - {self.get_channel_display()})"

    def render_message(self, context: dict) -> str:
        """
        Render the message template with provided context.

        Args:
            context: Dictionary with values for template placeholders

        Returns:
            str: Rendered message with placeholders replaced
        """
        message = self.message_body
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        return message
