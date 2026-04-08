from django.urls import path

from apps.chatbot.views import (
    ChatbotDashboardView,
    ChatbotSettingsDetailView,
    ChatbotSettingsUpdateView,
    ConversationHistoryView,
    TemplateCreateView,
    TemplateDeleteView,
    TemplateSyncView,
    WhatsAppWebhookView,
)

app_name = "apps.chatbot"

urlpatterns = [
    path(
        "webhook/whatsapp/",
        WhatsAppWebhookView.as_view(),
        name="whatsapp-webhook",
    ),
    path(
        "dashboard/",
        ChatbotDashboardView.as_view(),
        name="chatbot-dashboard",
    ),
    path(
        "settings/",
        ChatbotSettingsDetailView.as_view(),
        name="chatbot-settings-detail",
    ),
    path(
        "settings/edit/",
        ChatbotSettingsUpdateView.as_view(),
        name="chatbot-settings-edit",
    ),
    path(
        "templates/create/",
        TemplateCreateView.as_view(),
        name="template-create",
    ),
    # Keep old name "template-approve" so the dashboard JS doesn't break
    path(
        "templates/<int:pk>/approve/",
        TemplateSyncView.as_view(),
        name="template-approve",
    ),
    path(
        "templates/<int:pk>/delete/",
        TemplateDeleteView.as_view(),
        name="template-delete",
    ),
    path(
        "conversations/<int:pk>/history/",
        ConversationHistoryView.as_view(),
        name="conversation-history",
    ),
]
