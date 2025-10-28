from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType

from apps.partners import models


class PartnerAccessMixin(LoginRequiredMixin):
    """Mixin para restringir acceso solo al partner autenticado."""

    def get_partner(self):
        """Obtener el partner del usuario autenticado."""
        user = self.request.user
        if user.is_partner and hasattr(user, "partner"):
            return user.partner
        return None

    def get_queryset(self):
        """Filtrar queryset por el partner autenticado."""
        queryset = super().get_queryset()
        partner = self.get_partner()

        if partner and hasattr(queryset.model, "partner"):
            return queryset.filter(partner=partner)
        return queryset.order_by("-created")


class DocumentPartnerAccessMixin(LoginRequiredMixin):
    """
    Mixin to filter documents based on the authenticated partner.

    This mixin is specifically designed for models that use GenericForeignKey
    (like the Document model) to relate to Partner objects. It filters the
    queryset to show only documents where the related_object is the
    authenticated partner.
    """

    def get_partner(self):
        """
        Get the partner associated with the authenticated user.

        Returns:
            Partner instance if the user is a partner, None otherwise.
        """
        user = self.request.user
        if user.is_partner and hasattr(user, "partner"):
            return user.partner
        return None

    def get_queryset(self):
        """
        Filter queryset to show only documents related to the authenticated partner.

        This method filters documents using the GenericForeignKey relationship
        by matching content_type (Partner model) and object_id (partner's pk).

        Returns:
            Filtered queryset containing only documents related to the partner.
        """
        queryset = super().get_queryset()
        partner = self.get_partner()

        if partner:
            # Get the ContentType for the Partner model
            partner_content_type = ContentType.objects.get_for_model(models.Partner)

            # Filter documents by content_type and partner's pk
            return queryset.filter(
                content_type=partner_content_type, object_id=partner.pk
            )

        return queryset.order_by("-created")
