from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Updates ConversationMessage.intent field:
    - Removes IntentType choices constraint
    - Increases max_length from 50 to 100
    - Updates help_text to reflect tool-calling usage
    """

    dependencies = [
        ("chatbot", "0002_add_delivery_status_and_templates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversationmessage",
            name="intent",
            field=models.CharField(
                max_length=100,
                blank=True,
                default="",
                help_text="Tool name called by the agent, if any",
            ),
        ),
    ]
