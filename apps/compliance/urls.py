from django.urls import path

from apps.compliance import views

app_name = "apps.compliance"

urlpatterns = [
    # Contribution URLs
    path(
        "contributions/",
        views.ContributionListView.as_view(),
        name="contribution-list",
    ),
    path(
        "contributions/create/",
        views.ContributionCreateView.as_view(),
        name="contribution-create",
    ),
    path(
        "contributions/<int:pk>/",
        views.ContributionDetailView.as_view(),
        name="contribution-detail",
    ),
    path(
        "contributions/<int:pk>/edit/",
        views.ContributionUpdateView.as_view(),
        name="contribution-edit",
    ),
    path(
        "contributions/<int:pk>/delete/",
        views.ContributionDeleteView.as_view(),
        name="contribution-delete",
    ),
    
    # SocialSecurity URLs
    path(
        "social-security/",
        views.SocialSecurityListView.as_view(),
        name="social-security-list",
    ),
    path(
        "social-security/create/",
        views.SocialSecurityCreateView.as_view(),
        name="social-security-create",
    ),
    path(
        "social-security/<int:pk>/",
        views.SocialSecurityDetailView.as_view(),
        name="social-security-detail",
    ),
    path(
        "social-security/<int:pk>/edit/",
        views.SocialSecurityUpdateView.as_view(),
        name="social-security-edit",
    ),
    path(
        "social-security/<int:pk>/delete/",
        views.SocialSecurityDeleteView.as_view(),
        name="social-security-delete",
    ),
    
    # Penalty URLs
    path(
        "penalties/",
        views.PenaltyListView.as_view(),
        name="penalty-list",
    ),
    path(
        "penalties/create/",
        views.PenaltyCreateView.as_view(),
        name="penalty-create",
    ),
    path(
        "penalties/<int:pk>/",
        views.PenaltyDetailView.as_view(),
        name="penalty-detail",
    ),
    path(
        "penalties/<int:pk>/edit/",
        views.PenaltyUpdateView.as_view(),
        name="penalty-edit",
    ),
    path(
        "penalties/<int:pk>/delete/",
        views.PenaltyDeleteView.as_view(),
        name="penalty-delete",
    ),
]