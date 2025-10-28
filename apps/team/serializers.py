"""Serializers for team app API endpoints."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.team import models


class AreaWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Area instances.

    This serializer includes all writable fields for Area.
    """

    class Meta:
        model = models.Area
        fields = [
            "id",
            "name",
            "description",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {"help_text": _("Name of the area.")},
            "description": {
                "help_text": _("Description of the area."),
                "allow_blank": True,
            },
        }

    def validate_name(self, value: str) -> str:
        """
        Validate that area name is unique for new instances.

        Args:
            value: The name to validate

        Returns:
            The validated name

        Raises:
            serializers.ValidationError: If name already exists
        """
        # Check if this is an update operation
        instance = getattr(self, "instance", None)

        if instance and instance.name == value:
            # If updating and name hasn't changed, it's valid
            return value

        # Check if name already exists
        if models.Area.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                _("An area with this name already exists.")
            )

        return value


class AreaSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Area instances.

    Includes timestamps.
    """

    class Meta:
        model = models.Area
        fields = [
            "id",
            "name",
            "description",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "created",
            "modified",
        ]


class PositionWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Position instances.

    This serializer includes all writable fields for Position.
    """

    class Meta:
        model = models.Position
        fields = [
            "id",
            "name",
            "description",
            "area",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "name": {"help_text": _("Name of the position.")},
            "description": {
                "help_text": _("Description of the position."),
                "allow_blank": True,
            },
            "area": {"help_text": _("Area this position belongs to.")},
        }


class PositionSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Position instances.

    Includes area information and timestamps.
    """

    area_name = serializers.CharField(source="area.name", read_only=True)

    class Meta:
        model = models.Position
        fields = [
            "id",
            "name",
            "description",
            "area",
            "area_name",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "area_name",
            "created",
            "modified",
        ]


class EmployeeWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Employee instances.

    This serializer includes all writable fields.
    Location fields (country, region, subregion, city) and user are excluded.
    """

    class Meta:
        model = models.Employee
        fields = [
            "id",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "document_type",
            "document_number",
            "gender",
            "birth_date",
            "phone",
            "email",
            "address",
            "zip_code",
            "position",
            "status",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {"help_text": _("First name of the employee.")},
            "paternal_last_name": {"help_text": _("Paternal last name.")},
            "maternal_last_name": {"help_text": _("Maternal last name.")},
            "document_type": {"help_text": _("Type of identification document.")},
            "document_number": {"help_text": _("Document identification number.")},
            "gender": {"help_text": _("Gender of the employee.")},
            "birth_date": {"help_text": _("Date of birth.")},
            "phone": {"help_text": _("Phone number.")},
            "email": {"help_text": _("Email address.")},
            "address": {"help_text": _("Physical address.")},
            "zip_code": {"help_text": _("Postal code.")},
            "position": {"help_text": _("Position of the employee.")},
            "status": {"help_text": _("Current status of the employee.")},
        }

    def validate_document_number(self, value: str) -> str:
        """
        Validate that document_number is unique for new instances.

        Args:
            value: The document_number to validate

        Returns:
            The validated document_number

        Raises:
            serializers.ValidationError: If document_number already exists
        """
        # Check if this is an update operation
        instance = getattr(self, "instance", None)

        if instance and instance.document_number == value:
            # If updating and document_number hasn't changed, it's valid
            return value

        # Check if document_number already exists
        if models.Employee.objects.filter(document_number=value).exists():
            raise serializers.ValidationError(
                _("An employee with this document number already exists.")
            )

        return value

    def validate_email(self, value: str) -> str:
        """
        Validate that email is unique for new instances.

        Args:
            value: The email to validate

        Returns:
            The validated email

        Raises:
            serializers.ValidationError: If email already exists
        """
        # Check if this is an update operation
        instance = getattr(self, "instance", None)

        if instance and instance.email == value:
            # If updating and email hasn't changed, it's valid
            return value

        # Check if email already exists
        if models.Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("An employee with this email already exists.")
            )

        return value


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Employee instances.

    Includes display fields for: status, document_type, gender.
    Includes location name fields for: country, region, subregion, city.
    Includes position and area information.
    """

    # Read-only fields for location data
    country_name = serializers.CharField(
        source="country.name", read_only=True, allow_null=True
    )
    region_name = serializers.CharField(
        source="region.name", read_only=True, allow_null=True
    )
    subregion_name = serializers.CharField(
        source="subregion.name", read_only=True, allow_null=True
    )
    city_name = serializers.CharField(
        source="city.name", read_only=True, allow_null=True
    )

    # Position and area information
    position_name = serializers.CharField(source="position.name", read_only=True)
    area_name = serializers.CharField(source="position.area.name", read_only=True)

    # Display fields
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    document_type_display = serializers.CharField(
        source="get_document_type_display", read_only=True
    )
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    # Computed fields
    full_name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = models.Employee
        fields = [
            "id",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "document_type",
            "document_type_display",
            "document_number",
            "gender",
            "gender_display",
            "birth_date",
            "phone",
            "email",
            "address",
            "zip_code",
            "country_name",
            "region_name",
            "subregion_name",
            "city_name",
            "position",
            "position_name",
            "area_name",
            "status",
            "status_display",
            "full_name",
            "short_name",
            "age",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "country_name",
            "region_name",
            "subregion_name",
            "city_name",
            "position_name",
            "area_name",
            "status_display",
            "document_type_display",
            "gender_display",
            "full_name",
            "short_name",
            "age",
            "created",
            "modified",
        ]
