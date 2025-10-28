from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import choices as core_choices
from apps.core import models as core_models
from apps.partners import choices


class Applicant(core_models.Person, TimeStampedModel):
    external_id = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Unique external identifier for the applicant."),
    )
    status = models.IntegerField(
        choices=choices.ApplicantStatus.choices,
        default=choices.ApplicantStatus.PENDING,
        help_text=_("Current status of the applicant."),
    )

    class Meta:
        managed = False
        verbose_name = _("Applicant")
        verbose_name_plural = _("Applicants")
        ordering = ["first_name", "paternal_last_name"]

    def __str__(self):
        return f"{self.first_name} {self.paternal_last_name}"


class Prospect(core_models.BaseUserTracked, TimeStampedModel):
    document_type = models.CharField(
        max_length=20,
        choices=core_choices.DocumentType.choices,
        help_text=_("Type of identification document"),
    )
    document_number = models.CharField(
        max_length=20,
        help_text=_("Document identification number"),
    )

    # Personal Information
    first_name = models.CharField(
        max_length=100,
        help_text=_("First name of the prospect"),
    )
    last_name = models.CharField(
        max_length=100,
        help_text=_("Last name of the prospect"),
    )
    birth_date = models.DateField(
        help_text=_("Date of birth"),
    )
    email = models.EmailField(
        help_text=_("Email address"),
    )
    phone = models.CharField(
        max_length=20,
        help_text=_("Phone number"),
    )

    # Status and tracking
    status = models.IntegerField(
        choices=choices.ProspectStatus.choices,
        default=choices.ProspectStatus.NEW,
        help_text=_("Current status of the prospect"),
    )

    # Source tracking
    source = models.CharField(
        max_length=50,
        default="landing_page",
        help_text=_("Source of the prospect registration"),
    )

    # Additional metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address when the prospect registered"),
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_("Browser user agent when registered"),
    )

    # Follow-up information
    contacted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date and time when prospect was first contacted"),
    )
    assigned_to = models.ForeignKey(
        "team.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_prospects",
        help_text=_("Employee assigned to follow up with this prospect"),
    )
    notes = models.TextField(
        blank=True,
        help_text=_("Additional notes about the prospect"),
    )

    class Meta:
        managed = False
        ordering = ["-created"]
        verbose_name = _("Prospect")
        verbose_name_plural = _("Prospects")
        unique_together = [["document_type", "document_number"]]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self) -> str:
        """Return the full name of the prospect."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Calculate and return the age of the prospect."""
        today = timezone.now().date()
        return (
            today.year
            - self.birth_date.year
            - (
                (today.month, today.day)
                < (self.birth_date.month, self.birth_date.day)
            )
        )

    def mark_contacted(self, employee=None):
        """Mark the prospect as contacted."""
        self.contacted_at = timezone.now()
        if employee:
            self.assigned_to = employee
        if self.status == choices.ProspectStatus.NEW:
            self.status = choices.ProspectStatus.CONTACTED
        self.save(update_fields=["contacted_at", "assigned_to", "status"])


class Partner(core_models.Person, TimeStampedModel):
    """Model to store business partner information."""

    status = models.IntegerField(
        choices=choices.PartnerStatus.choices,
        default=choices.PartnerStatus.PENDING,
        help_text=_("Current status of the partner."),
    )

    class Meta:
        managed = False
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        ordering = ["first_name", "paternal_last_name"]

    def __str__(self):
        return f"{self.first_name} {self.paternal_last_name}"


class PartnerEmploymentInfo(core_models.BaseUserTracked, TimeStampedModel):
    """Model to store employment information for partners according to Peruvian labor regulations."""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name="employment_info",
        help_text=_("Partner associated with this employment information."),
    )

    # Occupation and Professional Information
    occupation = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Current occupation of the partner."),
    )
    profession = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Professional specialization or career."),
    )
    education_level = models.IntegerField(
        choices=choices.EducationLevel.choices,
        null=True,
        blank=True,
        help_text=_("Highest education level achieved."),
    )

    # Employment Type and Status
    employment_type = models.IntegerField(
        choices=choices.EmploymentType.choices,
        null=True,
        blank=True,
        help_text=_("Type of employment according to Peruvian labor law."),
    )
    is_currently_employed = models.BooleanField(
        default=False,
        help_text=_("Whether the partner is currently employed."),
    )

    # Workplace Information
    workplace_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Name of the current workplace or company."),
    )
    workplace_address = models.CharField(
        max_length=500,
        blank=True,
        help_text=_("Address of the current workplace."),
    )
    other_workplace = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Additional or secondary workplace."),
    )
    job_position = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Current job position or title."),
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Department or area within the company."),
    )

    # Contract Information
    contract_type = models.IntegerField(
        choices=choices.ContractType.choices,
        null=True,
        blank=True,
        help_text=_("Type of employment contract."),
    )
    contract_start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Start date of current employment contract."),
    )
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("End date of contract (if applicable)."),
    )
    work_schedule = models.IntegerField(
        choices=choices.WorkScheduleType.choices,
        null=True,
        blank=True,
        help_text=_("Type of work schedule."),
    )
    weekly_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Number of weekly working hours."),
    )

    # Income Information
    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Base salary amount in Peruvian Soles (PEN)."),
    )
    salary_frequency = models.IntegerField(
        choices=choices.SalaryFrequency.choices,
        null=True,
        blank=True,
        help_text=_("Frequency of salary payment."),
    )
    additional_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Additional income from bonuses, commissions, etc."),
    )
    total_monthly_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Total estimated monthly income."),
    )

    # Work Contact Information
    work_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Work phone number."),
    )
    work_email = models.EmailField(
        blank=True,
        help_text=_("Work email address."),
    )
    supervisor_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Name of direct supervisor or manager."),
    )

    # Additional Information
    notes = models.TextField(
        blank=True,
        help_text=_("Additional notes about employment information."),
    )

    class Meta:
        verbose_name = _("Partner Employment Information")
        verbose_name_plural = _("Partner Employment Information")
        ordering = ["partner__first_name", "partner__paternal_last_name"]

    def __str__(self):
        return f"Employment Info: {self.partner.full_name}"

    @property
    def is_formal_employment(self):
        """Check if this is formal employment (has contract)."""
        return (
            self.contract_type is not None
            and self.employment_type == choices.EmploymentType.DEPENDENT
        )
