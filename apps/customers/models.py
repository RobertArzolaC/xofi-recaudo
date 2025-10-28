from allauth.account.models import EmailAddress
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import SoftDeletableModel, TimeStampedModel

from apps.core import models as core_models
from apps.users import models as users_models


class Company(
    core_models.BaseAddress,
    core_models.BaseContact,
    core_models.BaseUserTracked,
    TimeStampedModel,
):
    logo = models.ImageField(
        upload_to="companies/",
        blank=True,
        null=True,
        help_text=_("Logo o foto de la empresa"),
    )
    tax_id = models.CharField(
        max_length=11,
        unique=True,
        help_text=_("RUC único de la empresa (11 dígitos)."),
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text=_("Nombre único de la empresa (mínimo 3 caracteres)."),
    )
    domain = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Dominio de la empresa (opcional)"),
    )

    class Meta:
        managed = False
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class Account(SoftDeletableModel, TimeStampedModel):
    user = models.OneToOneField(
        users_models.User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="account",
    )

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ("user__last_name", "user__first_name")

    def __str__(self):
        return self.user.get_full_name()

    @cached_property
    def full_name(self):
        return self.user.get_full_name()

    @cached_property
    def is_email_verified(self):
        return EmailAddress.objects.filter(
            user=self.user, verified=True
        ).exists()


class Agency(
    core_models.BaseAddress,
    core_models.BaseContact,
    core_models.BaseUserTracked,
    core_models.IsActive,
    core_models.NameDescription,
    TimeStampedModel,
):
    """
    Model representing an agency or branch office.
    """

    code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        help_text=_("Unique code for the agency"),
    )

    class Meta:
        managed = False
        ordering = ["name"]
        unique_together = ["code"]
        verbose_name = _("Agency")
        verbose_name_plural = _("Agencies")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
