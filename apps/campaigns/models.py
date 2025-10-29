from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.campaigns import choices, services
from apps.core import models as core_models
from apps.partners import services as partner_services


class Group(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent a group of partners for campaigns."""

    partners = models.ManyToManyField(
        "partners.Partner",
        related_name="campaign_groups",
        verbose_name=_("Partners"),
        blank=True,
        help_text=_("Partners included in this group."),
    )
    priority = models.IntegerField(
        _("Priority"),
        choices=choices.GroupPriority.choices,
        default=choices.GroupPriority.MEDIUM,
        help_text=_("Priority level of the group."),
    )

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name

    @property
    def partner_count(self):
        """Return the number of partners in the group."""
        return self.partners.count()

    @property
    def total_outstanding_debt(self):
        """Return the total overdue debt of all partners in the group."""

        return partner_services.PartnerDebtService.calculate_total_outstanding_debt(
            self.partners.all()
        )

    @property
    def overdue_obligations_count(self):
        """Return the total number of overdue obligations for partners in the group."""
        from apps.partners.services import PartnerDebtService

        return PartnerDebtService.count_overdue_obligations(self.partners.all())

    def get_debt_summary(self):
        """Return a detailed summary of overdue debts for partners in the group."""

        return partner_services.PartnerDebtService.get_debt_summary(
            self.partners.all()
        )

    def get_partners_debt_detail(self):
        """Return detailed debt information for each partner in the group."""

        return partner_services.PartnerDebtService.get_partners_debt_detail(
            self.partners.all()
        )


class Campaign(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to represent collection campaigns."""

    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="campaigns",
        verbose_name=_("Group"),
        null=True,
        blank=True,
        help_text=_("Group associated with this campaign."),
    )
    execution_date = models.DateTimeField(
        _("Execution Date"),
        null=True,
        blank=True,
        help_text=_("Date and time when the campaign will be executed."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=choices.CampaignStatus.choices,
        default=choices.CampaignStatus.DRAFT,
        help_text=_("Current status of the campaign."),
    )
    target_amount = models.DecimalField(
        _("Target Amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Target collection amount for the campaign."),
    )
    average_cost = models.DecimalField(
        _("Average Cost"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Average cost per notification for this campaign."),
    )
    use_payment_link = models.BooleanField(
        _("Use Payment Link"),
        default=False,
        help_text=_("Include payment link in campaign notifications."),
    )

    # Execution tracking fields
    is_processing = models.BooleanField(
        _("Is Processing"),
        default=False,
        help_text=_("Indicates if the campaign is currently being processed."),
    )
    last_execution_at = models.DateTimeField(
        _("Last Execution At"),
        null=True,
        blank=True,
        help_text=_("Date and time of the last execution attempt."),
    )
    execution_count = models.PositiveIntegerField(
        _("Execution Count"),
        default=0,
        help_text=_("Number of times this campaign has been executed."),
    )
    last_execution_result = models.TextField(
        _("Last Execution Result"),
        null=True,
        blank=True,
        help_text=_("Result message from the last execution attempt."),
    )

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Check if campaign is currently active."""
        return self.status == choices.CampaignStatus.ACTIVE

    @property
    def can_be_executed(self):
        """Check if campaign can be executed now."""

        return services.CampaignExecutionService.can_execute_campaign(self)

    def start_execution(self):
        """
        Mark campaign as being processed. Returns True if lock acquired, False otherwise.

        Transitions campaign status to PROCESSING state and sets execution tracking fields.
        This method ensures atomic execution through database-level locking.
        """

        return services.CampaignExecutionService.start_campaign_execution(self)

    def finish_execution(self, success=True, result_message=None):
        """
        Mark campaign execution as finished and transition to appropriate status.

        Flow after processing:
        - Success + notifications created → SENDING (ready to send notifications)
        - Success + no notifications → Return to original status
        - Success + all sent → COMPLETED
        - Failure → FAILED
        """

        services.CampaignExecutionService.finish_campaign_execution(
            self, success, result_message
        )

    def create_notifications_for_partners(
        self, notification_type, partners=None
    ):
        """Create notifications for specified partners or all partners in the group."""

        return services.CampaignNotificationService.create_notifications_for_partners(
            self, notification_type, partners
        )

    def get_notification_summary(self):
        """Get summary of notifications for this campaign."""

        return services.CampaignNotificationService.get_notification_summary(
            self
        )

    @property
    def notification_progress_percentage(self):
        """Get the percentage of notifications that have been processed."""

        return services.CampaignNotificationService.calculate_notification_progress_percentage(
            self
        )

    def should_be_completed(self):
        """Check if campaign should be marked as completed based on notification status."""

        summary = self.get_notification_summary()
        return services.CampaignExecutionService._should_be_completed(
            self, summary
        )

    @classmethod
    def get_status_flow_info(cls):
        """
        Get information about the campaign status flow and transitions.

        Returns:
            dict: Information about status flow, valid transitions, and descriptions
        """

        return services.CampaignStatusService.get_status_flow_info()

    def get_current_status_info(self):
        """Get information about the current status and possible next states."""

        return services.CampaignStatusService.get_current_status_info(self)


class CampaignNotification(
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to register notifications sent to partners during campaign execution."""

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Campaign"),
        help_text=_("Campaign that generated this notification."),
    )
    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.CASCADE,
        related_name="campaign_notifications",
        verbose_name=_("Partner"),
        help_text=_("Partner who received this notification."),
    )
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
    message_content = models.TextField(
        _("Message Content"),
        null=True,
        blank=True,
        help_text=_("Content of the notification message."),
    )
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
    error_message = models.TextField(
        _("Error Message"),
        null=True,
        blank=True,
        help_text=_("Error message if the notification failed to send."),
    )
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
            models.Index(fields=["campaign", "partner"]),
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["notification_type", "channel"]),
        ]
        unique_together = [
            ("campaign", "partner", "notification_type", "channel"),
        ]

    def __str__(self):
        return (
            f"{self.campaign.name} - {self.partner.full_name} - "
            f"{self.get_notification_type_display()} ({self.get_status_display()})"
        )

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
    """Model to store WhatsApp message templates for campaigns."""

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
        from apps.campaigns.services import MessageTemplateService

        return MessageTemplateService.render_template_message(self, context)
