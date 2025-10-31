from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.core.authentication import BearerTokenAuthentication
from apps.support import models, serializers


@extend_schema_view(
    create=extend_schema(
        summary="Create support ticket",
        description=(
            "Create a new support ticket from chatbot. "
            "The ticket will be automatically assigned to an available employee based on workload. "
            "If the partner has an associated agency, the ticket will be assigned to an employee from that agency."
        ),
        request=serializers.TicketCreateSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "subject": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                    "status": {"type": "string"},
                    "partner": {"type": "string"},
                    "assigned_to": {"type": "string", "nullable": True},
                    "created": {"type": "string", "format": "date-time"},
                },
            },
            400: {"description": "Invalid data provided"},
        },
        tags=["Support"],
    ),
)
class TicketViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Ticket model.

    Only allows creating tickets via API (for chatbot integration).
    Tickets are automatically assigned to available employees based on workload.
    """

    queryset = models.Ticket.objects.all()
    serializer_class = serializers.TicketCreateSerializer
    authentication_classes = [BearerTokenAuthentication]
    http_method_names = ["post", "head", "options"]

    def create(self, request, *args, **kwargs):
        """
        Create a new support ticket from chatbot.

        The ticket will be automatically assigned to the employee with the least workload.
        If the partner has an agency, only employees from that agency will be considered.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        """Save the ticket."""
        serializer.save()
