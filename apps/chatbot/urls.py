from django.urls import path

from apps.chatbot.views import (
    ChatbotSettingsDetailView,
    ChatbotSettingsUpdateView,
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
        "settings/",
        ChatbotSettingsDetailView.as_view(),
        name="chatbot-settings-detail",
    ),
    path(
        "settings/edit/",
        ChatbotSettingsUpdateView.as_view(),
        name="chatbot-settings-edit",
    ),
]
