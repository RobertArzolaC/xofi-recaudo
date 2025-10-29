from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.campaigns import choices
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
    start_date = models.DateField(
        _("Start Date"),
        null=True,
        blank=True,
        help_text=_("Date when the campaign starts."),
    )
    end_date = models.DateField(
        _("End Date"),
        null=True,
        blank=True,
        help_text=_("Date when the campaign ends."),
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

    # Execution schedule
    execution_time = models.TimeField(
        _("Execution Time"),
        null=True,
        blank=True,
        help_text=_(
            "Time of day when the campaign notifications will be sent."
        ),
    )

    # Notification configuration
    notify_3_days_before = models.BooleanField(
        _("Notify 3 Days Before"),
        default=False,
        help_text=_("Send notification 3 days before due date."),
    )
    notify_on_due_date = models.BooleanField(
        _("Notify on Due Date"),
        default=True,
        help_text=_("Send notification on the due date."),
    )
    notify_3_days_after = models.BooleanField(
        _("Notify 3 Days After"),
        default=False,
        help_text=_("Send notification 3 days after due date."),
    )
    notify_7_days_after = models.BooleanField(
        _("Notify 7 Days After"),
        default=False,
        help_text=_("Send notification 7 days after due date."),
    )
    use_payment_link = models.BooleanField(
        _("Use Payment Link"),
        default=False,
        help_text=_("Include payment link in campaign notifications."),
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

    def create_notifications_for_partners(
        self, notification_type, partners=None
    ):
        """Create notifications for specified partners or all partners in the group."""
        from apps.partners.services import PartnerDebtService

        if not self.group:
            return []

        if partners is None:
            partners = self.group.partners.all()

        notifications = []
        for partner in partners:
            partner_debt = PartnerDebtService.get_single_partner_debt_detail(
                partner
            )

            notification = CampaignNotification(
                campaign=self,
                partner=partner,
                notification_type=notification_type,
                channel=choices.NotificationChannel.WHATSAPP,  # Default channel
                recipient_email=partner.email,
                recipient_phone=partner.phone,
                total_debt_amount=partner_debt["total_debt"],
                included_payment_link=self.use_payment_link,
                created_by=self.created_by,
                modified_by=self.modified_by,
            )
            notifications.append(notification)

        # Bulk create notifications
        if notifications:
            CampaignNotification.objects.bulk_create(notifications)

        return notifications

    def get_notification_summary(self):
        """Get summary of notifications for this campaign."""
        from django.db.models import Count

        summary = self.notifications.aggregate(
            total=Count("id"),
            pending=Count(
                "id", filter=models.Q(status=choices.NotificationStatus.PENDING)
            ),
            sent=Count(
                "id", filter=models.Q(status=choices.NotificationStatus.SENT)
            ),
            failed=Count(
                "id", filter=models.Q(status=choices.NotificationStatus.FAILED)
            ),
        )

        return {
            "total_notifications": summary["total"] or 0,
            "pending_notifications": summary["pending"] or 0,
            "sent_notifications": summary["sent"] or 0,
            "failed_notifications": summary["failed"] or 0,
        }


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
            f"{self.campaign.name} - {self.partner.name} - "
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
