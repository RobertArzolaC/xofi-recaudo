from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.partners import choices, models


class PartnerAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Autocomplete view for partners."""

    def get_queryset(self):
        """Return filtered queryset based on search term."""

        qs = models.Partner.objects.filter(status=choices.PartnerStatus.ACTIVE)

        if self.q:
            qs = qs.filter(
                first_name__icontains=self.q,
                paternal_last_name__icontains=self.q,
                document_number__icontains=self.q,
            )

        return qs.order_by("first_name")
