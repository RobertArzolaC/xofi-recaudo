from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.partners.models import Partner
from apps.payments import choices, models


class PartnerPaymentSummarySerializer(serializers.Serializer):
    """Serializer for partner payment summary response."""

    # This is mainly for documentation purposes
    # The actual response is built in the view
    pass


class PaymentConceptAllocationSerializer(serializers.Serializer):
    """Serializer for creating payment concept allocations."""

    payment_id = serializers.IntegerField()
    concept_id = serializers.IntegerField()
    concept_type = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_payment_id(self, value):
        """Validate that payment exists."""
        try:
            models.Payment.objects.get(id=value)
        except models.Payment.DoesNotExist:
            raise serializers.ValidationError(_("Payment not found."))
        return value

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than 0."))
        return value


class ProcessPaymentSerializer(serializers.Serializer):
    """Serializer for processing payments with automatic allocation."""

    partner_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.CharField(required=False, default="CASH")
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    concept_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    concept_type = serializers.CharField(required=False, default="INSTALLMENT")

    def validate_partner_id(self, value):
        """Validate that partner exists."""
        try:
            Partner.objects.get(id=value)
        except Partner.DoesNotExist:
            raise serializers.ValidationError(_("Partner not found."))
        return value

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than 0."))
        return value


class AutoAllocatePaymentSerializer(serializers.Serializer):
    """Serializer for auto-allocating payments."""

    # This serializer is mainly for documentation
    # The payment ID comes from the URL
    pass


class PaymentSearchSerializer(serializers.ModelSerializer):
    """Serializer for payment search results."""

    partner_name = serializers.CharField(source="partner.full_name", read_only=True)
    concept_display = serializers.CharField(
        source="get_concept_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_allocated = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    unallocated_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = models.Payment
        fields = [
            "id",
            "payment_number",
            "partner_name",
            "concept",
            "concept_display",
            "due_date",
            "payment_date",
            "scheduled_amount",
            "paid_amount",
            "payment_method",
            "payment_method_display",
            "reference_number",
            "status",
            "status_display",
            "is_overdue",
            "remaining_amount",
            "total_allocated",
            "unallocated_amount",
            "created",
            "modified",
        ]


class PaymentConceptAllocationListSerializer(serializers.ModelSerializer):
    """Serializer for listing payment concept allocations."""

    payment_number = serializers.CharField(
        source="payment.payment_number", read_only=True
    )
    partner_name = serializers.CharField(
        source="payment.partner.full_name", read_only=True
    )
    concept_type = serializers.CharField(source="content_type.model", read_only=True)
    concept_object_str = serializers.CharField(source="concept_object", read_only=True)
    allocation_type_display = serializers.CharField(
        source="get_allocation_type_display", read_only=True
    )

    class Meta:
        model = models.PaymentConceptAllocation
        fields = [
            "id",
            "payment_number",
            "partner_name",
            "concept_type",
            "concept_object_str",
            "amount_applied",
            "allocation_type",
            "allocation_type_display",
            "application_date",
            "notes",
            "created",
        ]


class PaymentReceiptListSerializer(serializers.ModelSerializer):
    """Serializer for listing payment receipts."""

    partner_name = serializers.CharField(source="partner.full_name", read_only=True)
    partner_document = serializers.CharField(
        source="partner.document_number", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    validated_by_name = serializers.CharField(
        source="validated_by.full_name", read_only=True
    )

    class Meta:
        model = models.PaymentReceipt
        fields = [
            "id",
            "partner",
            "partner_name",
            "partner_document",
            "amount",
            "payment_date",
            "status",
            "status_display",
            "validated_by_name",
            "validated_at",
            "receipt_file",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "partner_name",
            "partner_document",
            "status_display",
            "validated_by_name",
            "validated_at",
            "created",
            "modified",
        ]


class PaymentReceiptDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment receipt detail."""

    partner_name = serializers.CharField(source="partner.full_name", read_only=True)
    partner_document = serializers.CharField(
        source="partner.document_number", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    validated_by_name = serializers.CharField(
        source="validated_by.full_name", read_only=True
    )
    payment_number = serializers.CharField(
        source="payment.payment_number", read_only=True
    )
    is_pending = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    is_rejected = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.PaymentReceipt
        fields = [
            "id",
            "partner",
            "partner_name",
            "partner_document",
            "payment",
            "payment_number",
            "receipt_file",
            "amount",
            "payment_date",
            "status",
            "status_display",
            "validation_notes",
            "validated_by",
            "validated_by_name",
            "validated_at",
            "notes",
            "is_pending",
            "is_approved",
            "is_rejected",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "partner_name",
            "partner_document",
            "payment_number",
            "status",
            "status_display",
            "validation_notes",
            "validated_by",
            "validated_by_name",
            "validated_at",
            "is_pending",
            "is_approved",
            "is_rejected",
            "created",
            "modified",
        ]


class PaymentReceiptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment receipts."""

    class Meta:
        model = models.PaymentReceipt
        fields = [
            "partner",
            "receipt_file",
            "amount",
            "payment_date",
            "notes",
        ]

    def validate_receipt_file(self, value):
        """Validate that the uploaded file is a valid format."""
        allowed_extensions = ["pdf", "jpg", "jpeg", "png"]
        file_extension = value.name.split(".")[-1].lower()

        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                _(
                    f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
                )
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                _("File size must not exceed 5MB.")
            )

        return value


class PaymentReceiptValidateSerializer(serializers.Serializer):
    """Serializer for validating (approving/rejecting) payment receipts."""

    action = serializers.ChoiceField(
        choices=["approve", "reject"],
        help_text=_("Action to perform: approve or reject"),
    )
    validation_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Notes about the validation"),
    )

    def validate(self, data):
        """Validate that rejection includes notes."""
        if data["action"] == "reject" and not data.get("validation_notes"):
            raise serializers.ValidationError(
                {"validation_notes": _("Validation notes are required when rejecting a receipt.")}
            )
        return data
