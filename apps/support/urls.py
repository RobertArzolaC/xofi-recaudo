from django.urls import path

from apps.support import views

app_name = "apps.support"


urlpatterns = [
    # Web URLs - Ticket Management
    path("tickets/", views.TicketListView.as_view(), name="ticket-list"),
    path(
        "ticket/<int:pk>/",
        views.TicketDetailView.as_view(),
        name="ticket-detail",
    ),
    path(
        "ticket/create/",
        views.TicketCreateView.as_view(),
        name="ticket-create",
    ),
    path(
        "ticket/<int:pk>/edit/",
        views.TicketUpdateView.as_view(),
        name="ticket-edit",
    ),
    path(
        "ticket/<int:pk>/delete/",
        views.TicketDeleteView.as_view(),
        name="ticket-delete",
    ),
    # Ticket actions
    path(
        "ticket/<int:pk>/comment/",
        views.TicketCommentCreateView.as_view(),
        name="ticket-comment-create",
    ),
    path(
        "ticket/<int:pk>/update-status/",
        views.TicketStatusUpdateView.as_view(),
        name="ticket-status-update",
    ),
]
