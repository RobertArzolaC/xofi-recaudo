from django.urls import path

from apps.campaigns import views

app_name = "apps.campaigns"

urlpatterns = [
    # Campaign URLs
    path("campaigns/", views.CampaignListView.as_view(), name="campaign-list"),
    path(
        "campaign/<int:pk>/",
        views.CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path(
        "campaign/create/",
        views.CampaignCreateView.as_view(),
        name="campaign-create",
    ),
    path(
        "campaign/<int:pk>/edit/",
        views.CampaignUpdateView.as_view(),
        name="campaign-edit",
    ),
    path(
        "campaign/<int:pk>/delete/",
        views.CampaignDeleteView.as_view(),
        name="campaign-delete",
    ),
    path(
        "campaign/<int:pk>/execute/",
        views.CampaignExecuteView.as_view(),
        name="campaign-execute",
    ),
    # Group URLs
    path("groups/", views.GroupListView.as_view(), name="group-list"),
    path(
        "group/<int:pk>/",
        views.GroupDetailView.as_view(),
        name="group-detail",
    ),
    path(
        "group/create/",
        views.GroupCreateView.as_view(),
        name="group-create",
    ),
    path(
        "group/<int:pk>/edit/",
        views.GroupUpdateView.as_view(),
        name="group-edit",
    ),
    path(
        "group/<int:pk>/delete/",
        views.GroupDeleteView.as_view(),
        name="group-delete",
    ),
    path(
        "group/<int:pk>/bulk-add-partners/",
        views.GroupBulkAddPartnersView.as_view(),
        name="group-bulk-add-partners",
    ),
    # AJAX URLs
    path(
        "ajax/group-debt/<int:group_id>/",
        views.GroupDebtAjaxView.as_view(),
        name="group-debt-ajax",
    ),
]
