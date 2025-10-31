from rest_framework import serializers

from apps.support import models


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tickets via API (chatbot)."""

    partner_document = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = models.Ticket
        fields = [
            "partner_document",
            "subject",
            "description",
            "priority",
        ]

    def validate_partner_document(self, value):
        """Validate that partner exists."""
        from apps.partners.models import Partner

        try:
            partner = Partner.objects.get(document_number=value)
            return partner
        except Partner.DoesNotExist:
            raise serializers.ValidationError("Partner with this document number does not exist.")

    def create(self, validated_data):
        """Create ticket and assign partner."""
        partner = validated_data.pop("partner_document")
        validated_data["partner"] = partner

        # Create ticket (auto-assignment will happen in model save method)
        ticket = models.Ticket.objects.create(**validated_data)
        return ticket

    def to_representation(self, instance):
        """Return detailed representation after creation."""
        return {
            "id": instance.id,
            "subject": instance.subject,
            "description": instance.description,
            "priority": instance.get_priority_display(),
            "status": instance.get_status_display(),
            "partner": instance.partner.full_name,
            "assigned_to": instance.assigned_to.full_name if instance.assigned_to else None,
            "created": instance.created,
        }
