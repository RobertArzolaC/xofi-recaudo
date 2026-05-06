from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.authentication import BearerTokenAuthentication
from apps.credits.choices import CreditStatus, InstallmentStatus
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

    def retrieve(self, request, pk=None, *args, **kwargs):
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
        credits = (
            partner.credits.filter(status=CreditStatus.ACTIVE)
            .select_related("product", "product__product_type")
            .order_by("-disbursement_date")
        )

        # Calculate summary statistics
        total_credits = credits.count()
        total_disbursed = credits.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        total_pending = credits.installments.filter(
            status__in=[
                InstallmentStatus.PENDING,
                InstallmentStatus.OVERDUE,
                InstallmentStatus.PARTIAL,
            ],
        ).aggregate(total_pending_amount=Sum("installment_amount"))[
            "total_pending_amount"
        ] or Decimal("0.00")

        # Calculate total payments
        total_payments = total_disbursed - total_pending

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
                    "payment_frequency": credit.get_payment_frequency_display().title()
                    if credit.payment_frequency
                    else None,
                    "outstanding_balance": float(credit.total_pending_amount),
                    "status": credit.get_status_display().title()
                    if credit.status
                    else None,
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
                    "total_outstanding": float(total_pending),
                    "active_credits_count": active_credits_count,
                },
                "credits": credit_details,
                "total_contributed": partner.total_contributed,
                "total_social_security_pending": partner.total_social_security_pending,
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
        credits = partner.credits.filter(
            status=CreditStatus.ACTIVE
        ).select_related("product", "product__product_type")

        # Calculate summary statistics
        active_credits_count = credits.count()
        total_disbursed = credits.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        total_outstanding = credits.installments.filter(
            status__in=[
                InstallmentStatus.PENDING,
                InstallmentStatus.OVERDUE,
                InstallmentStatus.PARTIAL,
            ],
        ).aggregate(total_pending_amount=Sum("installment_amount"))[
            "total_pending_amount"
        ] or Decimal("0.00")

        # Calculate total payments
        total_payments = total_disbursed - total_outstanding

        # Get unique product names
        associated_products_list = list(
            credits.values_list("product__name", flat=True).distinct()
        )
        associated_products = ", ".join(associated_products_list)

        # Build credit list (minimal)
        credit_list = []
        for credit in credits:
            credit_list.append(
                {
                    "id": credit.id,
                    "product_name": credit.product.name,
                    "amount": float(credit.amount),
                }
            )

        return Response(
            {
                "partner": {
                    "id": partner.id,
                    "full_name": partner.full_name,
                    "document_number": partner.document_number,
                },
                "summary": {
                    "active_credits_count": active_credits_count,
                    "total_outstanding": float(total_outstanding),
                    "total_payments": float(total_payments),
                    "associated_products": associated_products,
                },
                "credits": credit_list,
                "count": len(credit_list),
            }
        )

    @extend_schema(
        operation_id="partners_credit_detail",
        summary="Get credit detail (AI Agent)",
        description=(
            "Retrieve minimal credit information for the chatbot agent. "
            "Looks up credit by product name."
        ),
        parameters=[
            OpenApiParameter(
                name="product_name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Product name of the credit",
            ),
        ],
        tags=["Partners"],
    )
    @action(detail=True, methods=["get"], url_path="credit-detail")
    def credit_detail(self, request, pk=None):
        """
        Get minimal credit detail for chatbot templates.
        """
        import unicodedata

        partner = self.get_object()
        product_name = request.query_params.get("product_name")

        if not product_name:
            return Response(
                {"detail": _("Product name is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def normalize(s):
            if not s:
                return ""
            return (
                unicodedata.normalize("NFKD", s)
                .encode("ASCII", "ignore")
                .decode("utf-8")
                .lower()
            )

        normalized_target = normalize(product_name)
        credits = partner.credits.select_related("product").all()

        credit = next(
            (
                c
                for c in credits
                if normalize(c.product.name) == normalized_target
            ),
            None,
        )

        if not credit:
            return Response(
                {"detail": _("Credit not found for this product.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        installments = credit.get_current_installments()
        payment_amount = (
            installments[0].installment_amount if installments else None
        )
        overdue_count = sum(1 for i in installments if i.is_overdue)
        pending_count = sum(
            1 for i in installments if i.status in ["PENDING", "PARTIAL"]
        )

        return Response(
            {
                "product_name": credit.product.name,
                "amount": float(credit.amount),
                "outstanding_balance": float(credit.total_pending_amount),
                "payment_amount": float(payment_amount)
                if payment_amount
                else 0.0,
                "status": credit.get_status_display().title(),
                "term_duration": credit.term_duration,
                "payment_frequency": credit.get_payment_frequency_display().title(),
                "interest_rate": float(credit.interest_rate),
                "overdue_count": overdue_count,
                "pending_count": pending_count,
            }
        )

    @extend_schema(
        operation_id="partners_credit_schedule",
        summary="Get credit schedule (AI Agent)",
        description="Retrieve overdue and next installments for the chatbot schedule message.",
        parameters=[
            OpenApiParameter(
                name="product_name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Product name of the credit",
            ),
        ],
        tags=["Partners"],
    )
    @action(detail=True, methods=["get"], url_path="credit-schedule")
    def credit_schedule(self, request, pk=None):
        """
        Get credit schedule for chatbot.
        """
        import unicodedata

        partner = self.get_object()
        product_name = request.query_params.get("product_name")

        if not product_name:
            return Response(
                {"detail": _("Product name is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def normalize(s):
            if not s:
                return ""
            return (
                unicodedata.normalize("NFKD", s)
                .encode("ASCII", "ignore")
                .decode("utf-8")
                .lower()
            )

        normalized_target = normalize(product_name)
        credits = partner.credits.select_related("product").all()

        credit = next(
            (
                c
                for c in credits
                if normalize(c.product.name) == normalized_target
            ),
            None,
        )

        if not credit:
            return Response(
                {"detail": _("Credit not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        installments = credit.get_current_installments()

        overdue = []
        next_installments = []
        total_overdue_amount = 0.0

        MONTHS_ES = {
            1: "Ene",
            2: "Feb",
            3: "Mar",
            4: "Abr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Ago",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dic",
        }

        for inst in installments:
            data = {
                "number": inst.installment_number,
                "due_date": f"{inst.due_date.day:02d} {MONTHS_ES[inst.due_date.month]} {inst.due_date.year}",
                "amount": float(inst.installment_amount),
                "days_overdue": inst.days_overdue,
            }
            if inst.is_overdue:
                overdue.append(data)
                total_overdue_amount += data["amount"]
            elif (
                inst.status in ["PENDING", "PARTIAL"]
                and len(next_installments) < 3
            ):
                next_installments.append(data)

        return Response(
            {
                "product_name": credit.product.name,
                "overdue": overdue,
                "next_installments": next_installments,
                "total_overdue_amount": total_overdue_amount,
            }
        )
