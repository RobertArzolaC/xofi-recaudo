from apps.notifications import choices, constants


def calculate_countdown(notification_count: int, channel: str) -> int:
    """
    Calculate countdown time for finalize_campaign_status based on
    notification count and channel.

    Args:
        notification_count: Number of notifications to process
        channel: Notification channel (WHATSAPP, TELEGRAM, SMS, EMAIL)

    Returns:
        int: Countdown in seconds (minimum 30 seconds)
    """
    if channel == choices.NotificationChannel.WHATSAPP:
        seconds_per_notification = constants.WHATSAPP_SECONDS_PER_NOTIFICATION
    else:
        seconds_per_notification = constants.DEFAULT_SECONDS_PER_NOTIFICATION

    calculated_countdown = notification_count * seconds_per_notification
    return max(calculated_countdown, constants.MIN_COUNTDOWN_SECONDS)
