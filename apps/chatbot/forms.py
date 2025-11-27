from constance import config
from django import forms
from django.utils.translation import gettext_lazy as _


class ChatbotSettingsForm(forms.Form):
    """Form for managing chatbot settings via django-constance."""

    welcome_image = forms.ImageField(
        label=_("Welcome Image"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": ".png,.jpg,.jpeg",
            }
        ),
        help_text=_(
            "Image sent before the welcome message on WhatsApp. "
            "Only *.png, *.jpg and *.jpeg files are accepted."
        ),
    )

    welcome_message = forms.CharField(
        label=_("Welcome Message"),
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control form-control-solid",
                "rows": 12,
                "placeholder": _("Enter the welcome message for the chatbot"),
            }
        ),
        help_text=_(
            "Message displayed when a user starts a conversation with the chatbot."
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with current constance values."""
        super().__init__(*args, **kwargs)

        # Set initial values from constance
        self.fields["welcome_message"].initial = config.CHATBOT_WELCOME_MESSAGE

    def save(self):
        """Save form data to constance configuration."""
        from constance import config as constance_config

        # Save welcome message
        constance_config.CHATBOT_WELCOME_MESSAGE = self.cleaned_data[
            "welcome_message"
        ]

        # Save welcome image if provided
        welcome_image = self.cleaned_data.get("welcome_image")
        if welcome_image:
            # Save the image file using constance's file handling
            from django.core.files.storage import default_storage

            # Delete old image if exists
            old_image = constance_config.CHATBOT_WELCOME_IMAGE
            if old_image and default_storage.exists(f"constance/{old_image}"):
                default_storage.delete(f"constance/{old_image}")

            # Save new image
            default_storage.save(
                f"constance/{welcome_image.name}", welcome_image
            )
            # Store only the filename (constance adds 'constance/' prefix)
            constance_config.CHATBOT_WELCOME_IMAGE = welcome_image.name
