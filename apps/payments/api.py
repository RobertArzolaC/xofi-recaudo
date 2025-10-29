from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.partners.models import Partner
from apps.payments import models, serializers, utils


@extend_schema(exclude=True)
class PartnerPaymentSummaryAPIView(generics.RetrieveAPIView):
    """API view to get partner payment summary and pending debts."""

    serializer_class = serializers.PartnerPaymentSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Partner.objects.all()

    def retrieve(self, request, *args, **kwargs) -> Response:
        """Return partner payment summary as JSON."""
        partner = self.get_object()

        # Use manager method for payment summary
        partner_payments = models.Payment.objects.summary_by_partner_aggregate(
            partner
        )

        # Get pending debts using utils
        pending_debts = utils.get_partner_pending_debts(partner)

        # Calculate totals from pending debts
        overdue_count = (
            sum(1 for debt in pending_debts if debt["is_overdue"])
            if pending_debts
            else 0
        )

        data = {
            "partner_info": {
                "id": partner.pk,
                "full_name": partner.full_name,
                "document_type": partner.get_document_type_display(),
                "document_number": partner.document_number,
                "email": partner.email,
                "phone": partner.phone,
            },
            "payment_summary": {
                "total_amount": str(partner_payments.get("total_amount", 0)),
                "payment_count": partner_payments.get("count", 0),
                "overdue_count": overdue_count,
                "avg_amount": str(partner_payments.get("avg_amount", 0))
                if partner_payments.get("avg_amount")
                else "0.00",
            },
            "pending_debts": [
                {
                    "type": debt["type"],
                    "slug": debt["slug"],
                    "id": debt["id"],
                    "description": debt["description"],
                    "due_date": debt["due_date"].isoformat()
                    if debt["due_date"]
                    else None,
                    "amount": str(debt["amount"]),
                    "is_overdue": debt["is_overdue"],
                    "days_overdue": debt.get("days_overdue", 0),
                }
                for debt in pending_debts
            ],
        }

        return Response(data)


@extend_schema(exclude=True)
class PaymentConceptAllocationCreateAPIView(generics.CreateAPIView):
    """API view to allocate payment to concepts."""

    serializer_class = serializers.PaymentConceptAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.PaymentConceptAllocation.objects.all()

    def create(self, request, *args, **kwargs) -> Response:
        """Create a new payment concept allocation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get payment and concept object
        payment_id = serializer.validated_data["payment_id"]
        concept_id = serializer.validated_data["concept_id"]
        concept_type = serializer.validated_data["concept_type"]
        amount = serializer.validated_data.get("amount")
        notes = serializer.validated_data.get("notes", "")

        payment = get_object_or_404(models.Payment, id=payment_id)

        # Get the concept object based on type
        concept_object = utils.get_concept_object_by_type_and_id(
            concept_type, concept_id
        )
        if not concept_object:
            return Response(
                {"error": _("Invalid concept type or ID.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if allocation is valid
        can_allocate, message = payment.can_be_allocated_to_concept(
            concept_object, amount
        )
        if not can_allocate:
            return Response(
                {"error": message}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create the allocation using manager method
        try:
            allocation = models.PaymentConceptAllocation.objects.allocate_payment_to_concept(
                payment=payment,
                concept_object=concept_object,
                amount_applied=amount,
                allocation_type="FULL"
                if amount == payment.unallocated_amount
                else "PARTIAL",
                notes=notes,
            )

            return Response(
                {
                    "success": True,
                    "message": _("Payment allocated successfully."),
                    "allocation": {
                        "id": allocation.id,
                        "amount_applied": str(allocation.amount_applied),
                        "allocation_type": allocation.allocation_type,
                        "application_date": allocation.application_date.isoformat(),
                    },
                    "payment_updated": {
                        "total_allocated": str(payment.total_allocated),
                        "unallocated_amount": str(payment.unallocated_amount),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(exclude=True)
class ProcessPaymentAPIView(generics.CreateAPIView):
    """API view to process a payment with automatic allocation."""

    serializer_class = serializers.ProcessPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs) -> Response:
        """Process a payment with automatic allocation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Extract validated data
            partner_id = serializer.validated_data["partner_id"]
            amount = serializer.validated_data["amount"]
            payment_method = serializer.validated_data.get(
                "payment_method", "CASH"
            )
            reference_number = serializer.validated_data.get(
                "reference_number", ""
            )
            notes = serializer.validated_data.get("notes", "")
            concept_ids = serializer.validated_data.get("concept_ids", [])
            concept_type = serializer.validated_data.get(
                "concept_type", "INSTALLMENT"
            )

            partner = get_object_or_404(Partner, id=partner_id)

            # Process the payment using utils
            payment, allocations = utils.process_payment_with_allocations(
                partner=partner,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number,
                notes=notes,
                concept_ids=concept_ids,
                concept_type=concept_type,
            )

            return Response(
                {
                    "success": True,
                    "message": _("Payment processed successfully."),
                    "payment": {
                        "id": payment.id,
                        "payment_number": payment.payment_number,
                        "paid_amount": str(payment.paid_amount),
                        "status": payment.status,
                    },
                    "allocations": [
                        {
                            "id": allocation.id,
                            "amount_applied": str(allocation.amount_applied),
                            "concept_object": str(allocation.concept_object),
                        }
                        for allocation in allocations
                    ],
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(exclude=True)
class PaymentStatisticsAPIView(generics.GenericAPIView):
    """API view to get payment statistics."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        """Get payment statistics using manager methods."""
        try:
            # Use manager methods for statistics
            overall_summary = models.Payment.objects.summary_by_concept()
            overdue_payments = models.Payment.objects.overdue().count()
            pending_payments = models.Payment.objects.pending().count()
            paid_payments = models.Payment.objects.paid().count()

            stats = {
                "overall_summary": overall_summary,
                "counts": {
                    "overdue": overdue_payments,
                    "pending": pending_payments,
                    "paid": paid_payments,
                    "total": overdue_payments
                    + pending_payments
                    + paid_payments,
                },
            }

            # Get partner-specific stats if partner_id is provided
            partner_id = request.GET.get("partner_id")
            if partner_id:
                partner = get_object_or_404(Partner, id=partner_id)
                partner_stats = models.Payment.objects.summary_by_partner(
                    partner
                )
                stats["partner_stats"] = partner_stats

            return Response(stats)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(exclude=True)
class PaymentSearchAPIView(generics.ListAPIView):
    """API view to search payments with filtering."""

    serializer_class = serializers.PaymentSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get filtered queryset using manager methods."""
        # Start with base queryset from manager
        queryset = models.Payment.objects.select_related(
            "partner"
        ).prefetch_related("concept_allocations")

        # Apply filters based on query parameters
        partner_id = self.request.GET.get("partner_id")
        if partner_id:
            partner = get_object_or_404(Partner, id=partner_id)
            queryset = models.Payment.objects.for_partner(partner)

        concept = self.request.GET.get("concept")
        if concept:
            queryset = models.Payment.objects.by_concept(concept)

        status_filter = self.request.GET.get("status")
        if status_filter:
            if status_filter == "overdue":
                queryset = models.Payment.objects.overdue()
            elif status_filter == "pending":
                queryset = models.Payment.objects.pending()
            elif status_filter == "paid":
                queryset = models.Payment.objects.paid()

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(payment_number__icontains=search)
                | models.Q(partner__name__icontains=search)
                | models.Q(partner__email__icontains=search)
            )

        return queryset.order_by("-created")


@extend_schema(exclude=True)
class AutoAllocatePaymentAPIView(generics.UpdateAPIView):
    """API view to automatically allocate a payment to best matching concepts."""

    serializer_class = serializers.AutoAllocatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Payment.objects.all()

    def update(self, request, *args, **kwargs) -> Response:
        """Automatically allocate payment to best matching concepts."""
        payment = self.get_object()

        try:
            # Get available concepts for allocation
            available_concepts = utils.get_available_concepts_for_payment(
                payment
            )

            if not available_concepts:
                return Response(
                    {"error": _("No available concepts found for allocation.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Auto allocate payment
            allocations = utils.auto_allocate_payment_to_best_match(
                payment=payment, available_concepts=available_concepts
            )

            return Response(
                {
                    "success": True,
                    "message": _("Payment automatically allocated."),
                    "allocations": [
                        {
                            "id": allocation.id,
                            "amount_applied": str(allocation.amount_applied),
                            "concept_object": str(allocation.concept_object),
                            "allocation_type": allocation.allocation_type,
                        }
                        for allocation in allocations
                    ],
                    "payment_updated": {
                        "total_allocated": str(payment.total_allocated),
                        "unallocated_amount": str(payment.unallocated_amount),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(exclude=True)
class PaymentConceptAllocationListAPIView(generics.ListAPIView):
    """API view to list payment concept allocations."""

    serializer_class = serializers.PaymentConceptAllocationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get allocations using manager methods."""
        # Get payment ID from URL or query params
        payment_id = self.kwargs.get("payment_id") or self.request.GET.get(
            "payment_id"
        )

        if payment_id:
            payment = get_object_or_404(models.Payment, id=payment_id)
            return models.PaymentConceptAllocation.objects.for_payment(payment)

        # Get concept type filter
        concept_type = self.request.GET.get("concept_type")
        if concept_type:
            return models.PaymentConceptAllocation.objects.for_concept_type(
                concept_type
            )

        return models.PaymentConceptAllocation.objects.select_related(
            "payment", "content_type"
        ).order_by("-created")
