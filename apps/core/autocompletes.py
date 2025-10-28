from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from cities_light.models import City, Country, Region, SubRegion


class CountryAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Autocomplete view for countries."""

    def get_queryset(self):
        """Return filtered queryset based on search term."""
        qs = Country.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")


class RegionAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Autocomplete view for regions filtered by country."""

    def get_queryset(self):
        """Return filtered queryset based on country and search term."""
        qs = Region.objects.all()

        country = self.forwarded.get("country", None)
        if country:
            qs = qs.filter(country=country)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")


class SubRegionAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Autocomplete view for subregions filtered by region."""

    def get_queryset(self):
        """Return filtered queryset based on region and search term."""
        qs = SubRegion.objects.all()

        region = self.forwarded.get("region", None)
        if region:
            qs = qs.filter(region=region)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")


class CityAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Autocomplete view for cities filtered by country, region, or subregion."""

    def get_queryset(self):
        """Return filtered queryset based on location hierarchy and search term."""
        qs = City.objects.all()

        country = self.forwarded.get("country", None)
        if country:
            qs = qs.filter(country=country)

        region = self.forwarded.get("region", None)
        if region:
            qs = qs.filter(region=region)

        subregion = self.forwarded.get("subregion", None)
        if subregion:
            qs = qs.filter(subregion=subregion)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")
