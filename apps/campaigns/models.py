from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.campaigns import choices, services
from apps.core import models as core_models
from apps.partners import services as partner_services


class BaseCampaign(
    core_models.NameDescription,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """
    Modelo base abstracto para todas las campañas.

    Contiene los campos y comportamientos comunes a todos los tipos de campañas.
    """

    # Campos comunes a todas las campañas
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
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=choices.NotificationChannel.choices,
        default=choices.NotificationChannel.TELEGRAM,
        help_text=_("Communication channel for campaign notifications."),
    )
    use_payment_link = models.BooleanField(
        _("Use Payment Link"),
        default=False,
        help_text=_("Include payment link in campaign notifications."),
    )
    average_cost = models.DecimalField(
        _("Average Cost"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Average cost per notification for this campaign."),
    )
    target_amount = models.DecimalField(
        _("Target Amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Target collection amount for the campaign."),
    )

    # Campos de seguimiento de ejecución
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

    # Campo discriminador para identificar el tipo de campaña
    campaign_type = models.CharField(
        _("Campaign Type"),
        max_length=20,
        choices=choices.CampaignType.choices,
        default=choices.CampaignType.GROUP,
        help_text=_("Type of campaign (auto-populated)."),
    )

    class Meta:
        abstract = True
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    # Métodos comunes (pueden ser sobrescritos en subclases)
    @property
    def is_active(self):
        """Check if campaign is currently active."""
        return self.status == choices.CampaignStatus.ACTIVE

    def start_execution(self):
        """Mark campaign as being processed."""
        # Implementación común o puede ser abstracta
        raise NotImplementedError("Subclasses must implement start_execution()")

    def finish_execution(self, success=True, result_message=None):
        """Mark campaign execution as finished."""
        raise NotImplementedError(
            "Subclasses must implement finish_execution()"
        )

    def get_notification_summary(self):
        """Get summary of notifications for this campaign."""
        raise NotImplementedError(
            "Subclasses must implement get_notification_summary()"
        )


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

    def start_execution(self):
        """Mark group as being processed."""
        self.status = choices.CampaignStatus.ACTIVE
        self.save(update_fields=["status"])

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
    BaseCampaign,
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

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Auto-populate campaign_type."""
        self.campaign_type = choices.CampaignType.GROUP
        super().save(*args, **kwargs)

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


class CampaignCSVFile(
    BaseCampaign,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    """Model to store CSV/Excel files uploaded for file-based campaigns."""

    file = models.FileField(
        _("File"),
        null=True,
        blank=True,
        upload_to="campaigns/csv/%Y/%m/%d/",
        help_text=_("Uploaded CSV or Excel file with contacts and amounts."),
    )
    # Proceso de validación de contactos
    validation_status = models.CharField(
        _("Validation Status"),
        max_length=20,
        choices=choices.ValidationStatus.choices,
        default=choices.ValidationStatus.PENDING,
        help_text=_("Status of contacts validation."),
    )
    validation_result = models.JSONField(
        _("Validation Result"),
        null=True,
        blank=True,
        help_text=_("Detailed validation results and errors."),
    )
    validated_at = models.DateTimeField(
        _("Validated At"),
        null=True,
        blank=True,
        help_text=_("Date and time when validation was completed."),
    )
    # Statistics de validación
    total_contacts = models.PositiveIntegerField(
        _("Total Contacts"),
        default=0,
        help_text=_("Total number of contacts in the CSV file."),
    )
    valid_contacts = models.PositiveIntegerField(
        _("Valid Contacts"),
        default=0,
        help_text=_("Number of valid contacts after validation."),
    )
    invalid_contacts = models.PositiveIntegerField(
        _("Invalid Contacts"),
        default=0,
        help_text=_("Number of invalid contacts after validation."),
    )

    class Meta:
        verbose_name = _("Campaign CSV/Excel File")
        verbose_name_plural = _("Campaign CSV/Excel Files")
        ordering = ["-created"]

    def __str__(self):
        return f"File for {self.campaign.name} ({self.get_validation_status_display()})"

    def save(self, *args, **kwargs):
        """Auto-populate campaign_type."""
        self.campaign_type = choices.CampaignType.FILE
        super().save(*args, **kwargs)

    @property
    def can_be_executed(self):
        """
        CSV campaigns can only be executed if validated.
        """
        return (
            self.validation_status == choices.ValidationStatus.VALIDATED
            and self.valid_contacts > 0
            and self.status
            in [
                choices.CampaignStatus.ACTIVE,
                choices.CampaignStatus.SCHEDULED,
            ]
            and not self.is_processing
            and self.execution_date is not None
        )

    @property
    def is_validated(self):
        """Check if CSV has been validated successfully."""
        return self.validation_status == choices.ValidationStatus.VALIDATED

    @property
    def validation_progress_percentage(self):
        """Calculate validation progress percentage."""
        if self.total_contacts == 0:
            return 0
        return round((self.valid_contacts / self.total_contacts) * 100, 2)

    def validate_csv_file(self):
        """
        Validate the uploaded CSV file.

        This method should:
        1. Parse the CSV file
        2. Validate each contact (format, required fields)
        3. Validate custom amounts
        4. Store validation results
        5. Update validation_status
        """
        from apps.campaigns.services import CSVValidationService

        return CSVValidationService.validate_campaign_csv(self)

    def create_notifications_from_csv(self):
        """
        Create notifications for all valid contacts in the CSV.

        Only creates notifications if validation is successful.
        """
        if not self.is_validated:
            raise ValueError(
                "Campaign must be validated before creating notifications"
            )

        from apps.campaigns.services import CSVCampaignNotificationService

        return CSVCampaignNotificationService.create_notifications_from_csv(
            self
        )


class CSVContact(TimeStampedModel):
    """
    Modelo para almacenar contactos individuales de campañas CSV.

    Almacena la información de cada contacto del CSV, incluyendo
    montos personalizados y estado de validación.
    """

    campaign = models.ForeignKey(
        CampaignCSVFile,
        on_delete=models.CASCADE,
        related_name="csv_contacts",
        verbose_name=_("Campaign"),
        help_text=_("CSV campaign this contact belongs to."),
    )

    full_name = models.CharField(
        _("Full Name"),
        max_length=200,
        help_text=_("Contact's full name."),
    )
    email = models.EmailField(
        _("Email"),
        null=True,
        blank=True,
        help_text=_("Contact's email address."),
    )
    phone = models.CharField(
        _("Phone"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Contact's phone number."),
    )
    document_number = models.CharField(
        _("Document Number"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Contact's document number (DNI, RUC, etc.)."),
    )
    amount = models.DecimalField(
        _("Amount"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Amount to collect from this contact."),
    )

    additional_data = models.JSONField(
        _("Additional Data"),
        null=True,
        blank=True,
        help_text=_("Additional fields from CSV (key-value pairs)."),
    )

    is_valid = models.BooleanField(
        _("Is Valid"),
        default=False,
        help_text=_("Whether this contact passed validation."),
    )
    validation_errors = models.JSONField(
        _("Validation Errors"),
        null=True,
        blank=True,
        help_text=_("List of validation errors for this contact."),
    )
    row_number = models.PositiveIntegerField(
        _("Row Number"),
        help_text=_("Row number in the original CSV file."),
    )

    class Meta:
        verbose_name = _("CSV Contact")
        verbose_name_plural = _("CSV Contacts")
        ordering = ["row_number"]
        indexes = [
            models.Index(fields=["campaign", "is_valid"]),
            models.Index(fields=["document_number"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"{self.full_name} - Row {self.row_number}"
