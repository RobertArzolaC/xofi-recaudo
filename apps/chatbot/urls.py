from django.urls import path

from apps.chatbot.views import WhatsAppWebhookView

app_name = "apps.chatbot"

urlpatterns = [
    path(
        "webhook/whatsapp/",
        WhatsAppWebhookView.as_view(),
        name="whatsapp-webhook",
    ),
]
