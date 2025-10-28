from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _

from apps.compliance import models as compliance_models
from apps.credits import models as credit_models
from apps.partners import models as partner_models
from apps.payments import models


class PaymentAllocationMixin:
    """Mixin to handle payment allocation processing."""

    def _extract_allocations_from_request(self):
        """Extract allocation data from the request."""
        allocations_data = []

        # The JavaScript sends allocation data as allocations[index][field]
        allocation_indices = set()
        for key in self.request.POST.keys():
            if key.startswith("allocations[") and "][" in key:
                index = key.split("[")[1].split("]")[0]
                try:
                    allocation_indices.add(int(index))
                except ValueError:
                    continue

        for index in sorted(allocation_indices):
            allocation_type = self.request.POST.get(f"allocations[{index}][type]")
            object_id = self.request.POST.get(f"allocations[{index}][object_id]")
            amount = self.request.POST.get(f"allocations[{index}][amount]")
            slug = self.request.POST.get(f"allocations[{index}][slug]")

            if allocation_type and object_id and amount:
                try:
                    allocations_data.append(
                        {
                            "type": allocation_type,
                            "object_id": int(object_id),
                            "amount": float(amount),
                            "slug": slug,
                        }
                    )
                except (ValueError, TypeError):
                    # Skip invalid allocation data
                    continue

        return allocations_data

    def _create_payment_allocations(self, allocations_data):
        """Create PaymentConceptAllocation records."""
        created_allocations = []

        for allocation_data in allocations_data:
            # Get the concept object based on type
            concept_object = self._get_concept_object(
                allocation_data["slug"], allocation_data["object_id"]
            )

            if concept_object:
                # Create the allocation
                allocation = models.PaymentConceptAllocation.objects.allocate_payment_to_concept(
                    payment=self.object,
                    concept_object=concept_object,
                    amount_applied=allocation_data["amount"],
                    allocation_type="FULL"
                    if allocation_data["amount"] == getattr(concept_object, "amount", 0)
                    else "PARTIAL",
                    notes=f"{_('Allocated via payment form')} - {allocation_data['type']}",
                )
                created_allocations.append(allocation)

        return created_allocations

    def _get_concept_object(self, concept_type, object_id):
        """Get concept object based on type and ID."""
        concept_type_lower = concept_type.lower()

        try:
            if concept_type_lower == "installment":
                return credit_models.Installment.objects.get(id=object_id)
            elif concept_type_lower == "contribution":
                return compliance_models.Contribution.objects.get(id=object_id)
            elif concept_type_lower == "social_security":
                return compliance_models.SocialSecurity.objects.get(id=object_id)
            elif concept_type_lower == "penalty":
                return compliance_models.Penalty.objects.get(id=object_id)
        except (ImportError, AttributeError):
            pass
        except Exception:
            pass

        return None


class PartnerPaymentMixin(LoginRequiredMixin):
    """
    Mixin to ensure user is associated with a partner account.

    This mixin validates that the logged-in user has an associated
    partner account before allowing access to partner-specific views.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check if user has an associated partner account."""
        if not hasattr(request.user, "partner") or not request.user.partner:
            messages.error(
                request,
                _("You must be registered as a partner to access this page."),
            )
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get_partner(self) -> partner_models.Partner:
        """Get the partner associated with the current user."""
        return self.request.user.partner
