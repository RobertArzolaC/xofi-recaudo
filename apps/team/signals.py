import logging

from django.contrib.auth.hashers import get_random_string
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.team import choices, models
from apps.users import models as user_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.Employee)
def create_user_for_employee(
    sender, instance: models.Employee, created: bool, **kwargs
) -> None:
    """
    Signal to automatically create a User when an Employee is created without an associated user.

    Args:
        sender: The model class that sent the signal
        instance: The Employee instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if created and not instance.user and instance.email:
        # Create user with employee information using email as primary identifier
        random_password = get_random_string(12)
        user = user_models.User.objects.create_user(
            email=instance.email,
            first_name=instance.first_name,
            last_name=f"{instance.paternal_last_name} {instance.maternal_last_name}".strip(),
            is_active=(instance.status == choices.EmployeeStatus.ACTIVE),
            password=random_password,
            is_staff=True,
        )

        # Associate the user with the employee
        instance.user = user
        # Use update to avoid triggering the signal again
        models.Employee.objects.filter(pk=instance.pk).update(user=user)

        logger.info(f"Created user {user.email} for employee {instance.id}")


@receiver(post_save, sender=models.Employee)
def sync_user_data_from_employee(
    sender, instance: models.Employee, created: bool, **kwargs
) -> None:
    """
    Signal to sync User data when Employee information is updated.
    Also activates the user account when Employee status changes to ACTIVE.

    Args:
        sender: The model class that sent the signal
        instance: The Employee instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if instance.user:
        # Track if any user field needs updating
        user_updated = False

        # Sync email
        if instance.user.email != instance.email:
            instance.user.email = instance.email
            user_updated = True

        # Sync first_name
        if instance.user.first_name != instance.first_name:
            instance.user.first_name = instance.first_name
            user_updated = True

        # Sync last_name (combination of paternal and maternal last names)
        expected_last_name = (
            f"{instance.paternal_last_name} {instance.maternal_last_name}".strip()
        )
        if instance.user.last_name != expected_last_name:
            instance.user.last_name = expected_last_name
            user_updated = True

        # Sync is_active based on employee status
        expected_is_active = instance.status == choices.EmployeeStatus.ACTIVE
        if instance.user.is_active != expected_is_active:
            instance.user.is_active = expected_is_active
            user_updated = True
            logger.info(
                f"User {instance.user.email} active status changed to {expected_is_active} "
                f"for employee {instance.id} (status: {instance.get_status_display()})"
            )

        # Save user if any field was updated
        if user_updated:
            instance.user.save(
                update_fields=["email", "first_name", "last_name", "is_active"]
            )


@receiver(post_delete, sender=models.Employee)
def delete_user_when_employee_deleted(
    sender, instance: models.Employee, **kwargs
) -> None:
    """
    Signal to delete the associated User when an Employee is deleted.

    Args:
        sender: The model class that sent the signal
        instance: The Employee instance being deleted
        **kwargs: Additional signal arguments
    """
    if instance.user:
        try:
            user_email = instance.user.email
            instance.user.delete()
            logger.info(f"Deleted user {user_email} for employee {instance.id}")
        except Exception:
            logger.exception(
                f"Failed to delete user {instance.user.id} for employee {instance.id}"
            )
