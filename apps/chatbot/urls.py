from django.urls import path

from apps.chatbot.views import (
    ChatbotDashboardView,
    ChatbotSettingsDetailView,
    ChatbotSettingsUpdateView,
    WhatsAppWebhookView,
    TemplateCreateView,
    TemplateApproveView,
    ChatbotTestView,
)

app_name = "apps.chatbot"

urlpatterns = [
    path(
        "test/",
        ChatbotTestView.as_view(),
        name="chatbot-test",
    ),
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
    path(
        "templates/<int:pk>/approve/",
        TemplateApproveView.as_view(),
        name="template-approve",
    ),
]
