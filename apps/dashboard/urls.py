from django.urls import path

from apps.dashboard import views

app_name = "apps.dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    # Chatbot admin
    path(
        "chatbot/",
        views.AdminChatbotDashboardView.as_view(),
        name="admin_chatbot_dashboard",
    ),
    path(
        "chatbot/conversations/",
        views.AdminChatbotConversationsView.as_view(),
        name="admin_chatbot_conversations",
    ),
    path(
        "chatbot/conversations/pending-status/",
        views.AdminChatbotConversationsPendingStatusView.as_view(),
        name="admin_chatbot_conversations_pending_status",
    ),
    path(
        "chatbot/conversations/<int:pk>/",
        views.AdminChatbotConversationDetailView.as_view(),
        name="admin_chatbot_conversation_detail",
    ),
    path(
        "chatbot/templates/",
        views.AdminChatbotTemplatesView.as_view(),
        name="admin_chatbot_templates",
    ),
    path(
        "chatbot/templates/send-test/",
        views.AdminChatbotSendTestTemplateView.as_view(),
        name="admin_chatbot_send_test_template",
    ),
]
