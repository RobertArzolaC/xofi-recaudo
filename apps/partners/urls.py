from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.partners import autocompletes, views, viewsets

app_name = "apps.partners"

# API Router
router = DefaultRouter()
router.register(r"partners", viewsets.PartnerViewSet, basename="partner")

urlpatterns = [
    # API URLs
    path("api/", include(router.urls)),
    # Web URLs
    # Applicant URLs
    path(
        "applicants/", views.ApplicantListView.as_view(), name="applicant-list"
    ),
    path(
        "applicant/<int:pk>/",
        views.ApplicantDetailView.as_view(),
        name="applicant-detail",
    ),
    path(
        "applicant/create/",
        views.ApplicantCreateView.as_view(),
        name="applicant-create",
    ),
    path(
        "applicant/<int:pk>/edit/",
        views.ApplicantUpdateView.as_view(),
        name="applicant-edit",
    ),
    path(
        "applicant/<int:pk>/delete/",
        views.ApplicantDeleteView.as_view(),
        name="applicant-delete",
    ),
    # Partner URLs
    path("partners/", views.PartnerListView.as_view(), name="partner-list"),
    path(
        "partner/<int:pk>/",
        views.PartnerDetailView.as_view(),
        name="partner-detail",
    ),
    path(
        "partner/create/",
        views.PartnerCreateView.as_view(),
        name="partner-create",
    ),
    path(
        "partner/<int:pk>/edit/",
        views.PartnerUpdateView.as_view(),
        name="partner-edit",
    ),
    path(
        "partner/<int:pk>/employment/",
        views.PartnerEmploymentUpdateView.as_view(),
        name="partner-employment",
    ),
    path(
        "partner/<int:pk>/delete/",
        views.PartnerDeleteView.as_view(),
        name="partner-delete",
    ),
    # Prospect URLs
    path("prospects/", views.ProspectListView.as_view(), name="prospect-list"),
    path(
        "prospect/<int:pk>/",
        views.ProspectDetailView.as_view(),
        name="prospect-detail",
    ),
    path(
        "prospect/<int:pk>/edit/",
        views.ProspectUpdateView.as_view(),
        name="prospect-edit",
    ),
    # Autocomplete URLs
    path(
        "autocomplete/partner/",
        autocompletes.PartnerAutocomplete.as_view(),
        name="partner-autocomplete",
    ),
]
