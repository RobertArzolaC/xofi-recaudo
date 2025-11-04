import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram.ext import Application

from apps.chatbot.channels.telegram import setup_handlers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to run the Telegram AI agent bot."""

    help = "Run the Telegram AI agent bot"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--polling",
            action="store_true",
            help="Use polling instead of webhook",
        )
        parser.add_argument(
            "--webhook-url",
            type=str,
            help="Webhook URL for receiving updates",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        token = settings.TELEGRAM_BOT_TOKEN

        if not token:
            self.stdout.write(
                self.style.ERROR(
                    "TELEGRAM_BOT_TOKEN not configured in settings"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS("Starting Telegram AI Agent Bot...")
        )

        # Create application
        application = Application.builder().token(token).build()

        # Setup handlers
        setup_handlers(application)

        # Run bot
        if options["polling"] or not options.get("webhook_url"):
            self.stdout.write(
                self.style.SUCCESS("Running bot in polling mode...")
            )
            application.run_polling(
                allowed_updates=["message", "edited_message"]
            )
        else:
            webhook_url = options["webhook_url"]
            self.stdout.write(
                self.style.SUCCESS(f"Setting up webhook at {webhook_url}")
            )
            application.run_webhook(
                listen="0.0.0.0",
                port=8443,
                webhook_url=webhook_url,
            )
