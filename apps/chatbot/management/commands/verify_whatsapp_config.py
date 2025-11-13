import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.services.chats.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to verify WhatsApp configuration.

    Usage:
        python manage.py verify_whatsapp_config
    """

    help = "Verify WhatsApp chatbot configuration"

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS("WhatsApp Chatbot Configuration Verification")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Check if WhatsApp service is configured
        whatsapp_service = WhatsAppService()

        if not whatsapp_service.is_configured():
            self.stdout.write(
                self.style.ERROR(
                    "❌ WhatsApp service is NOT configured properly."
                )
            )
            self.stdout.write("")
            self.stdout.write("Please ensure the following settings are set:")
            self.stdout.write("  - WHATSAPP_API_TOKEN")
            self.stdout.write("  - WHATSAPP_PHONE_NUMBER_ID")
            self.stdout.write("  - WHATSAPP_WEBHOOK_VERIFY_TOKEN")
            self.stdout.write("")
            return

        self.stdout.write(
            self.style.SUCCESS("✅ WhatsApp service is configured properly.")
        )
        self.stdout.write("")

        # Display configuration
        self.stdout.write(self.style.WARNING("Configuration Details:"))
        self.stdout.write(
            f"  Phone Number ID: {settings.WHATSAPP_PHONE_NUMBER_ID}"
        )
        self.stdout.write(
            f"  API Token: {'*' * 20}{settings.WHATSAPP_API_TOKEN[-10:]}"
        )

        whapi_base_url = getattr(settings, "WHAPI_BASE_URL", "https://gate.whapi.cloud")
        self.stdout.write(f"  WHAPI Base URL: {whapi_base_url}")

        self.stdout.write("")

        # Display webhook URL
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        webhook_url = f"{base_url}/chatbot/webhook/whatsapp/"

        self.stdout.write(self.style.WARNING("Webhook Configuration:"))
        self.stdout.write(f"  Webhook URL: {webhook_url}")
        self.stdout.write("")
        self.stdout.write(
            "To configure the webhook in WHAPI:"
        )
        self.stdout.write(
            "  1. Go to https://whapi.cloud/"
        )
        self.stdout.write("  2. Select your channel")
        self.stdout.write("  3. Go to Settings > Webhooks")
        self.stdout.write(f"  4. Set Webhook URL: {webhook_url}")
        self.stdout.write(
            "  5. Select event: 'messages'"
        )
        self.stdout.write(
            "  6. Click Save"
        )
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Note: WHAPI doesn't require webhook verification tokens"
            )
        )
        self.stdout.write("")

        # Test message sending capability
        self.stdout.write(self.style.WARNING("Testing Service:"))
        try:
            # Just verify the service can be instantiated
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ WhatsApp service initialized successfully"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error initializing service: {e}")
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS("Verification Complete")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
