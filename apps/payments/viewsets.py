from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.authentication import BearerTokenAuthentication
from apps.payments import models, serializers


@extend_schema_view(
    create=extend_schema(
        summary="Upload a payment receipt",
        description=(
            "Upload a new payment receipt. Accepts PDF, JPG, or PNG files up to 5MB. "
            "The receipt will be set to PENDING status and will require validation by an employee."
        ),
        tags=["Payment Receipts"],
    ),
)
class PaymentReceiptViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Payment Receipt management.

    Provides endpoint for uploading payment receipts.
    """

    queryset = models.PaymentReceipt.objects.select_related(
        "partner", "payment", "validated_by"
    )
    authentication_classes = [BearerTokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = serializers.PaymentReceiptCreateSerializer

    # Only allow POST
    http_method_names = ["post", "head", "options"]

    def perform_create(self, serializer):
        """Set created_by when creating a receipt."""
        serializer.save(created_by=self.request.user)

    def create(self, request):
        """Create a new payment receipt."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return_serializer = serializers.PaymentReceiptDetailSerializer(
            serializer.instance
        )
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)
