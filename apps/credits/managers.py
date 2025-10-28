from django.db import models


class CreditQuerySet(models.QuerySet):
    """Custom QuerySet for Credit model."""

    def with_current_installments(self):
        """
        Prefetch current installments for credits based on their current_version.

        Returns:
            CreditQuerySet: QuerySet with prefetched current installments.
        """
        from apps.credits.models import Installment

        return self.prefetch_related(
            models.Prefetch(
                "installments",
                queryset=Installment.objects.select_related("credit").order_by(
                    "due_date"
                ),
                to_attr="current_installments_cache",
            )
        )


class CreditManager(models.Manager):
    """Custom Manager for Credit model."""

    def get_queryset(self):
        """
        Get the custom QuerySet for Credit model.

        Returns:
            CreditQuerySet: Custom QuerySet instance.
        """
        return CreditQuerySet(self.model, using=self._db)

    def with_current_installments(self):
        """
        Get credits with their current installments prefetched.

        Returns:
            CreditQuerySet: QuerySet with prefetched current installments.
        """
        return self.get_queryset().with_current_installments()
