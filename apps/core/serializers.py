from rest_framework import serializers


class CountrySerializer(serializers.Serializer):
    """Serializer for Country information (read-only)."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class RegionSerializer(serializers.Serializer):
    """Serializer for Region information (read-only)."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class SubRegionSerializer(serializers.Serializer):
    """Serializer for SubRegion information (read-only)."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class CitySerializer(serializers.Serializer):
    """Serializer for City information (read-only)."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
