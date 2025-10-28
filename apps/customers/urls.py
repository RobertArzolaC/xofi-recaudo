from django.urls import path

from apps.customers import views

app_name = "apps.customers"

urlpatterns = [
    # Accounts URLs
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path(
        "accounts/create/",
        views.AccountCreateView.as_view(),
        name="account_create",
    ),
    path(
        "accounts/update/<int:pk>/",
        views.AccountUpdateView.as_view(),
        name="account_update",
    ),
    path(
        "accounts/<int:pk>/delete/",
        views.AccountDeleteView.as_view(),
        name="account_delete",
    ),
    # Company URLs
    path(
        "company/<int:pk>/",
        views.CompanyDetailView.as_view(),
        name="company-detail",
    ),
    path(
        "company/<int:pk>/edit/",
        views.CompanyUpdateView.as_view(),
        name="company-edit",
    ),
    # Agency URLs
    path("agencies/", views.AgencyListView.as_view(), name="agency-list"),
    path(
        "agencies/create/",
        views.AgencyCreateView.as_view(),
        name="agency-create",
    ),
    path(
        "agencies/<int:pk>/",
        views.AgencyDetailView.as_view(),
        name="agency-detail",
    ),
    path(
        "agencies/<int:pk>/edit/",
        views.AgencyUpdateView.as_view(),
        name="agency-edit",
    ),
    path(
        "agencies/<int:pk>/delete/",
        views.AgencyDeleteView.as_view(),
        name="agency-delete",
    ),
    # Autocomplete URLs
    path(
        "agency-autocomplete/",
        views.AgencyAutocomplete.as_view(),
        name="agency-autocomplete",
    ),
]
