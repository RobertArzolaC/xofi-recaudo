from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.core import serializers as core_serializers
from apps.partners import models


class PartnerEmploymentInfoSerializer(serializers.ModelSerializer):
    """Serializer for Partner Employment Information."""

    class Meta:
        model = models.PartnerEmploymentInfo
        fields = [
            "id",
            "occupation",
            "profession",
            "education_level",
            "employment_type",
            "is_currently_employed",
            "workplace_name",
            "workplace_address",
            "other_workplace",
            "job_position",
            "department",
            "contract_type",
            "contract_start_date",
            "contract_end_date",
            "work_schedule",
            "weekly_hours",
            "base_salary",
            "salary_frequency",
            "additional_income",
            "total_monthly_income",
            "work_phone",
            "work_email",
            "supervisor_name",
            "notes",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class PartnerListSerializer(serializers.ModelSerializer):
    """Serializer for listing partners."""

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Partner
        fields = [
            "id",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "full_name",
            "document_type",
            "document_number",
            "phone",
            "email",
            "status",
            "age",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "full_name", "age", "created", "modified"]


class PartnerDetailSerializer(serializers.ModelSerializer):
    """Serializer for partner detail with nested relationships."""

    full_name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    country = core_serializers.CountrySerializer(read_only=True)
    region = core_serializers.RegionSerializer(read_only=True)
    subregion = core_serializers.SubRegionSerializer(read_only=True)
    city = core_serializers.CitySerializer(read_only=True)
    employment_info = PartnerEmploymentInfoSerializer(read_only=True)

    class Meta:
        model = models.Partner
        fields = [
            "id",
            "first_name",
            "paternal_last_name",
            "maternal_last_name",
            "full_name",
            "short_name",
            "initials",
            "document_type",
            "document_number",
            "gender",
            "birth_date",
            "age",
            "phone",
            "email",
            "address",
            "zip_code",
            "country",
            "region",
            "subregion",
            "city",
            "status",
            "employment_info",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "short_name",
            "initials",
            "age",
            "country",
            "region",
            "subregion",
            "city",
            "employment_info",
            "created",
            "modified",
        ]


class PartnerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating partners."""

    class Meta:
        model = models.Partner
        fields = [
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
            "status",
        ]

    def validate_document_number(self, value):
        """Validate that document number is unique."""
        instance = self.instance
        if (
            models.Partner.objects.filter(document_number=value)
            .exclude(pk=instance.pk if instance else None)
            .exists()
        ):
            raise serializers.ValidationError(
                _("A partner with this document number already exists.")
            )
        return value
