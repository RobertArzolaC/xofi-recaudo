from django.urls import path

from apps.core import autocompletes

app_name = "apps.core"

urlpatterns = [
    # Autocomplete URLs
    path(
        "autocomplete/country/",
        autocompletes.CountryAutocomplete.as_view(),
        name="country-autocomplete",
    ),
    path(
        "autocomplete/region/",
        autocompletes.RegionAutocomplete.as_view(),
        name="region-autocomplete",
    ),
    path(
        "autocomplete/subregion/",
        autocompletes.SubRegionAutocomplete.as_view(),
        name="subregion-autocomplete",
    ),
    path(
        "autocomplete/city/",
        autocompletes.CityAutocomplete.as_view(),
        name="city-autocomplete",
    ),
]
