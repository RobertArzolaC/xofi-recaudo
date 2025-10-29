from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.authentication import BearerTokenAuthentication
from apps.partners import models, serializers


@extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve partner details",
        description="Get detailed information about a specific partner by ID, document number, or phone.",
        tags=["Partners"],
    ),
)
class PartnerViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Partner model.

    Provides read-only endpoints for partner information and related data.
    Supports querying by ID, document_number, or phone.
    """

    queryset = models.Partner.objects.all()
    authentication_classes = [BearerTokenAuthentication]
    lookup_field = "pk"
    serializer_class = serializers.PartnerDetailSerializer

    # Disable CRUD operations
    http_method_names = ["get", "head", "options"]

    def get_object(self):
        """
        Override to support lookup by id, document_number, or phone.

        The lookup_value parameter from URL can be:
        - An integer (ID)
        - A document number
        - A phone number
        """
        lookup_value = self.kwargs.get(self.lookup_field)

        # Try to find by ID first
        if lookup_value.isdigit():
            queryset = self.filter_queryset(self.get_queryset())
            obj = get_object_or_404(queryset, pk=int(lookup_value))
            self.check_object_permissions(self.request, obj)
            return obj

        # Try to find by document_number or phone
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(
            queryset, Q(document_number=lookup_value) | Q(phone=lookup_value)
        )
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request):
        """
        Retrieve partner details.

        Supports lookup by ID, document_number, or phone.
        """
        partner = self.get_object()
        serializer = self.get_serializer(partner)
        return Response(serializer.data)

    @extend_schema(
        operation_id="partners_account_statement",
        summary="Get partner's account statement",
        description=(
            "Retrieve the account statement for a specific partner, including "
            "total credits, total payments, outstanding balance, and detailed "
            "credit information with payment status."
        ),
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
                description="Partner ID, document number, or phone number",
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "partner": {"type": "object"},
                    "summary": {
                        "type": "object",
                        "properties": {
                            "total_credits": {"type": "number"},
                            "total_disbursed": {"type": "number"},
                            "total_payments": {"type": "number"},
                            "total_outstanding": {"type": "number"},
                            "active_credits_count": {"type": "integer"},
                        },
                    },
                    "credits": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
            }
        },
        tags=["Partners"],
    )
    @action(detail=True, methods=["get"], url_path="account-statement")
    def account_statement(self, request, pk=None):
        """
        Get the account statement for a partner.

        Returns:
            - Partner information
            - Summary of credits and payments
            - Detailed list of credits with payment information
        """
        partner = self.get_object()

        # Get all credits for this partner
        credits = partner.credits.select_related("product", "product__product_type")

        # Calculate summary statistics
        total_credits = credits.count()
        total_disbursed = (
            credits.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        )
        total_outstanding = (
            credits.aggregate(total=Sum("outstanding_balance"))["total"]
            or Decimal("0.00")
        )

        # Calculate total payments
        total_payments = (
            partner.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        )

        # Count active credits
        active_credits_count = credits.filter(status="ACTIVE").count()

        # Build credit details
        credit_details = []
        for credit in credits:
            credit_details.append(
                {
                    "id": credit.id,
                    "product": credit.product.name,
                    "product_type": credit.product.product_type.name,
                    "amount": float(credit.amount),
                    "interest_rate": float(credit.interest_rate),
                    "term_duration": credit.term_duration,
                    "payment_frequency": credit.payment_frequency,
                    "outstanding_balance": float(credit.outstanding_balance),
                    "status": credit.status,
                    "application_date": (
                        credit.application_date.isoformat()
                        if credit.application_date
                        else None
                    ),
                    "approval_date": (
                        credit.approval_date.isoformat()
                        if credit.approval_date
                        else None
                    ),
                    "disbursement_date": (
                        credit.disbursement_date.isoformat()
                        if credit.disbursement_date
                        else None
                    ),
                }
            )

        return Response(
            {
                "partner": {
                    "id": partner.id,
                    "full_name": partner.full_name,
                    "document_number": partner.document_number,
                    "phone": partner.phone,
                    "email": partner.email,
                },
                "summary": {
                    "total_credits": total_credits,
                    "total_disbursed": float(total_disbursed),
                    "total_payments": float(total_payments),
                    "total_outstanding": float(total_outstanding),
                    "active_credits_count": active_credits_count,
                },
                "credits": credit_details,
            }
        )

    @extend_schema(
        operation_id="partners_credits_list",
        summary="List partner's credits",
        description=(
            "Retrieve a list of all credits (loans) associated with a specific partner."
        ),
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
                description="Partner ID, document number, or phone number",
            ),
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter credits by status (e.g., ACTIVE, PENDING, COMPLETED)",
                required=False,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "partner": {"type": "object"},
                    "credits": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
            }
        },
        tags=["Partners"],
    )
    @action(detail=True, methods=["get"], url_path="credits")
    def list_credits(self, request, pk=None):
        """
        List all credits for a specific partner.

        Query Parameters:
            - status: Filter credits by status
        """
        partner = self.get_object()

        # Get credits queryset
        credits = partner.credits.select_related("product", "product__product_type")

        # Apply status filter if provided
        status_filter = request.query_params.get("status", None)
        if status_filter:
            credits = credits.filter(status=status_filter.upper())

        # Build credit list
        credit_list = []
        for credit in credits:
            credit_list.append(
                {
                    "id": credit.id,
                    "product": {
                        "id": credit.product.id,
                        "name": credit.product.name,
                        "product_type": credit.product.product_type.name,
                    },
                    "amount": float(credit.amount),
                    "interest_rate": float(credit.interest_rate),
                    "term_duration": credit.term_duration,
                    "payment_frequency": credit.payment_frequency,
                    "payment_amount": (
                        float(credit.payment_amount) if credit.payment_amount else None
                    ),
                    "outstanding_balance": float(credit.outstanding_balance),
                    "status": credit.status,
                    "application_date": (
                        credit.application_date.isoformat()
                        if credit.application_date
                        else None
                    ),
                    "approval_date": (
                        credit.approval_date.isoformat()
                        if credit.approval_date
                        else None
                    ),
                    "disbursement_date": (
                        credit.disbursement_date.isoformat()
                        if credit.disbursement_date
                        else None
                    ),
                    "created": credit.created.isoformat(),
                    "modified": credit.modified.isoformat(),
                }
            )

        return Response(
            {
                "partner": {
                    "id": partner.id,
                    "full_name": partner.full_name,
                    "document_number": partner.document_number,
                },
                "credits": credit_list,
                "count": len(credit_list),
            }
        )

    @extend_schema(
        operation_id="partners_credit_detail",
        summary="Get credit detail",
        description=(
            "Retrieve detailed information about a specific credit for a partner, "
            "including installment schedule and payment history."
        ),
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
                description="Partner ID, document number, or phone number",
            ),
            OpenApiParameter(
                name="credit_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="Credit ID",
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "partner": {"type": "object"},
                    "credit": {"type": "object"},
                    "installments": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "payments": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
            },
            404: {"description": "Credit not found"},
        },
        tags=["Partners"],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="credits/(?P<credit_id>[^/.]+)",
    )
    def credit_detail(self, request, pk=None, credit_id=None):
        """
        Get detailed information about a specific credit.

        Returns:
            - Partner information
            - Credit details
            - Installment schedule
            - Payment history
        """
        partner = self.get_object()

        # Get the specific credit
        try:
            credit = partner.credits.select_related(
                "product", "product__product_type"
            ).get(id=credit_id)
        except models.Partner.credits.rel.related_model.DoesNotExist:
            return Response(
                {"detail": _("Credit not found for this partner.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get installments for current version
        installments = credit.get_current_installments()

        # Build installment list
        installment_list = []
        for installment in installments:
            installment_list.append(
                {
                    "id": installment.id,
                    "installment_number": installment.installment_number,
                    "due_date": installment.due_date.isoformat(),
                    "installment_amount": float(installment.installment_amount),
                    "principal_amount": float(installment.principal_amount),
                    "interest_amount": float(installment.interest_amount),
                    "balance_after": float(installment.balance_after),
                    "status": installment.status,
                    "payment_date": (
                        installment.payment_date.isoformat()
                        if installment.payment_date
                        else None
                    ),
                    "amount_paid": float(installment.amount_paid),
                    "remaining_balance": float(installment.remaining_balance),
                    "is_overdue": installment.is_overdue,
                    "days_overdue": installment.days_overdue,
                }
            )

        # Get payments for this credit (via installment allocations)
        from apps.credits.models import Installment

        credit_installment_ids = Installment.objects.filter(credit=credit).values_list(
            "id", flat=True
        )

        # Get payment allocations for these installments
        from apps.payments.models import PaymentConceptAllocation
        from django.contrib.contenttypes.models import ContentType

        installment_content_type = ContentType.objects.get_for_model(Installment)

        payment_allocations = PaymentConceptAllocation.objects.filter(
            content_type=installment_content_type, object_id__in=credit_installment_ids
        ).select_related("payment")

        # Build payment list
        payment_list = []
        seen_payment_ids = set()

        for allocation in payment_allocations:
            if allocation.payment.id not in seen_payment_ids:
                seen_payment_ids.add(allocation.payment.id)
                payment_list.append(
                    {
                        "id": allocation.payment.id,
                        "payment_number": allocation.payment.payment_number,
                        "payment_date": allocation.payment.payment_date.isoformat(),
                        "amount": float(allocation.payment.amount),
                        "payment_method": allocation.payment.payment_method,
                        "reference_number": allocation.payment.reference_number,
                        "status": allocation.payment.status,
                    }
                )

        return Response(
            {
                "partner": {
                    "id": partner.id,
                    "full_name": partner.full_name,
                    "document_number": partner.document_number,
                },
                "credit": {
                    "id": credit.id,
                    "product": {
                        "id": credit.product.id,
                        "name": credit.product.name,
                        "product_type": credit.product.product_type.name,
                    },
                    "amount": float(credit.amount),
                    "interest_rate": float(credit.interest_rate),
                    "term_duration": credit.term_duration,
                    "delinquency_rate": float(credit.delinquency_rate),
                    "payment_frequency": credit.payment_frequency,
                    "payment_amount": (
                        float(credit.payment_amount) if credit.payment_amount else None
                    ),
                    "outstanding_balance": float(credit.outstanding_balance),
                    "status": credit.status,
                    "application_date": (
                        credit.application_date.isoformat()
                        if credit.application_date
                        else None
                    ),
                    "approval_date": (
                        credit.approval_date.isoformat()
                        if credit.approval_date
                        else None
                    ),
                    "disbursement_date": (
                        credit.disbursement_date.isoformat()
                        if credit.disbursement_date
                        else None
                    ),
                    "total_interest": float(credit.total_interest),
                    "total_repayment": float(credit.total_repayment),
                    "current_version": credit.current_version,
                    "notes": credit.notes,
                    "created": credit.created.isoformat(),
                    "modified": credit.modified.isoformat(),
                },
                "installments": installment_list,
                "payments": payment_list,
                "summary": {
                    "total_installments": len(installment_list),
                    "paid_installments": sum(
                        1 for i in installment_list if i["status"] == "PAID"
                    ),
                    "pending_installments": sum(
                        1 for i in installment_list if i["status"] == "PENDING"
                    ),
                    "overdue_installments": sum(
                        1 for i in installment_list if i["is_overdue"]
                    ),
                    "total_payments": len(payment_list),
                    "total_paid": sum(p["amount"] for p in payment_list),
                },
            }
        )
