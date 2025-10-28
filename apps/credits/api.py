import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.credits import choices, models

logger = logging.getLogger(__name__)


class CreditSummaryAPIView(APIView):
    """
    API view to get credit summary for AJAX requests.

    Returns credit details to display as a summary when selected in forms.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, credit_id):
        """Get credit summary by ID."""
        try:
            credit = models.Credit.objects.select_related(
                "partner", "product", "product__product_type"
            ).get(id=credit_id)

            data = {
                "id": credit.id,
                "partner": {
                    "id": credit.partner.id,
                    "full_name": credit.partner.full_name,
                    "document_number": getattr(
                        credit.partner, "document_number", ""
                    ),
                },
                "product": {
                    "id": credit.product.id,
                    "name": credit.product.name,
                    "product_type": credit.product.product_type.name,
                },
                "amount": {
                    "value": float(credit.amount),
                    "formatted": f"${credit.amount:,.2f}",
                },
                "outstanding_balance": {
                    "value": float(credit.outstanding_balance),
                    "formatted": f"${credit.outstanding_balance:,.2f}",
                },
                "interest_rate": {
                    "value": float(credit.interest_rate),
                    "formatted": f"{credit.interest_rate}%",
                },
                "term_duration": {
                    "value": credit.term_duration,
                    "formatted": f"{credit.term_duration}",
                },
                "payment_frequency": {
                    "value": credit.payment_frequency,
                    "display": credit.get_payment_frequency_display(),
                },
                "payment_amount": {
                    "value": float(credit.payment_amount)
                    if credit.payment_amount
                    else 0,
                    "formatted": f"${credit.payment_amount:,.2f}"
                    if credit.payment_amount
                    else "N/A",
                },
                "status": {
                    "value": credit.status,
                    "display": credit.get_status_display(),
                },
                "application_date": credit.application_date.isoformat()
                if credit.application_date
                else None,
                "approval_date": credit.approval_date.isoformat()
                if credit.approval_date
                else None,
                "disbursement_date": credit.disbursement_date.isoformat()
                if credit.disbursement_date
                else None,
                "notes": "",
                "pending_installments": credit.installments.filter(
                    status__in=[
                        choices.InstallmentStatus.PENDING,
                        choices.InstallmentStatus.OVERDUE,
                        choices.InstallmentStatus.PARTIAL,
                    ]
                ).count(),
                "total_installments": credit.installments.count(),
            }

            return Response(data, status=status.HTTP_200_OK)

        except models.Credit.DoesNotExist:
            return Response(
                {"error": "Credit not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("Error fetching credit data: %s", e)
            return Response(
                {"error": "An error occurred while fetching credit data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProductSummaryAPIView(APIView):
    """
    API view to get product summary for AJAX requests.

    Returns product details to display as a summary when selected in forms.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        """Get product summary by ID."""
        try:
            product = models.Product.objects.select_related("product_type").get(
                id=product_id, is_active=True
            )

            data = {
                "id": product.id,
                "name": product.name,
                "product_type": {
                    "id": product.product_type.id,
                    "name": product.product_type.name,
                },
                "description": product.description or "",
                "amount_range": {
                    "min": float(product.min_amount),
                    "max": float(product.max_amount),
                    "formatted": f"${product.min_amount:,.2f} - ${product.max_amount:,.2f}",
                },
                "interest_rate_range": {
                    "min": float(product.min_interest_rate),
                    "max": float(product.max_interest_rate),
                    "formatted": f"{product.min_interest_rate}% - {product.max_interest_rate}%",
                },
                "interest_type": {
                    "value": product.interest_type,
                    "display": product.get_interest_type_display(),
                },
                "term_range": {
                    "min": product.min_term_duration,
                    "max": product.max_term_duration,
                    "formatted": f"{product.min_term_duration} - {product.max_term_duration} months",
                },
                "payment_frequency": {
                    "value": product.payment_frequency,
                    "display": product.get_payment_frequency_display(),
                },
                "delinquency_rate_range": {
                    "min": float(product.min_delinquency_rate),
                    "max": float(product.max_delinquency_rate),
                    "formatted": f"{product.min_delinquency_rate}% - {product.max_delinquency_rate}%",
                },
                "is_active": product.is_active,
            }

            return Response(data, status=status.HTTP_200_OK)

        except models.Product.DoesNotExist:
            return Response(
                {"error": "Product not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("Error fetching product data: %s", e)
            return Response(
                {"error": "An error occurred while fetching product data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
