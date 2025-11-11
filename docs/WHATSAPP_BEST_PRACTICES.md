# WhatsApp Best Practices Implementation

This document describes the implementation of WHAPI.cloud best practices to avoid WhatsApp bans when sending campaign notifications.

## Overview

The system implements comprehensive rate limiting and behavioral guidelines recommended by WHAPI to prevent account blocking when sending WhatsApp messages at scale.

**Reference**: [WHAPI - How to Not Get Banned](https://support.whapi.cloud/help-desk/blocking/how-to-not-get-banned)

## Implemented Features

### 1. Rate Limiting Service

**File**: `apps/notifications/services/whatsapp_rate_limiter.py`

The `WhatsAppRateLimiter` service implements the following restrictions:

#### Message Volume Limits
- **Per-minute limit**: 6-12 messages maximum
- **Daily activity**: Maximum 6 hours of sending activity per day
- **Consecutive days**: Avoid sending more than 3 consecutive days

#### Implementation Details
```python
from apps.notifications.services import WhatsAppRateLimiter

# Check if message can be sent
rate_check = WhatsAppRateLimiter.can_send_message()
if rate_check['allowed']:
    # Send message
    send_message()
    # Record the sent message
    WhatsAppRateLimiter.record_message_sent()
else:
    # Wait before retry
    wait_seconds = rate_check['wait_seconds']
    retry_later(wait_seconds)
```

#### Cache Keys
The service uses Django cache to track:
- `whatsapp:rate:minute:{YYYYMMDDHHMM}` - Messages sent in current minute
- `whatsapp:rate:daily:{YYYYMMDD}` - Active minutes in current day
- `whatsapp:rate:consecutive_days` - Count of consecutive active days
- `whatsapp:rate:last_message` - Timestamp of last message sent

### 2. Human-like Behavior

**File**: `apps/notifications/providers/whatsapp/whapi.py`

The WHAPI provider implements human-like sending patterns:

#### Typing Indicators
- Sends "typing..." indicator before each message
- Simulates real user behavior
- Endpoint: `POST /messages/presence`

#### Random Delays
- 5-10 second random delay between messages
- Avoids pattern detection by WhatsApp algorithms
- Implemented in `get_random_delay()` method

#### HTTPS Links
- Automatically converts HTTP links to HTTPS
- Required by WhatsApp for security

### 3. Campaign Settings

**Migration**: `apps/campaigns/migrations/0004_add_whatsapp_campaign_settings.py`

New fields added to `Campaign` and `CampaignCSVFile` models:

#### Available Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `whatsapp_personalize_messages` | Boolean | True | Personalize each WhatsApp message to avoid spam detection |
| `whatsapp_include_stop_command` | Boolean | True | Include "write STOP to stop receiving messages" |
| `whatsapp_avoid_unsolicited_links` | Boolean | True | Avoid sending payment links in first message |
| `whatsapp_group_by_region` | Boolean | False | Group contacts by region to avoid international clustering |
| `whatsapp_target_response_rate` | Decimal | 30.0 | Target response rate percentage (recommended: 30%) |

### 4. Task-Level Rate Limiting

**File**: `apps/notifications/tasks.py`

The `send_notification` task checks rate limits before sending WhatsApp messages:

```python
@shared_task(name="notifications.send_notification")
def send_notification(self, notification_id: int):
    notification = CampaignNotification.objects.get(id=notification_id)

    # Check WhatsApp rate limits
    if notification.channel == NotificationChannel.WHATSAPP:
        rate_check = WhatsAppRateLimiter.can_send_message()
        if not rate_check['allowed']:
            # Retry after wait period
            raise self.retry(countdown=rate_check['wait_seconds'])

    # Send notification
    result = NotificationSenderService.send_notification(notification)
```

## WHAPI Best Practices Coverage

### ✅ Implemented

1. **Message Volume & Rate Limiting**
   - ✅ Limit to 6-12 messages per minute
   - ✅ Maximum 6 hours activity per day
   - ✅ Avoid more than 3 consecutive days
   - ✅ Randomized intervals between messages

2. **User Interaction Signals**
   - ✅ Typing indicators before sending
   - ✅ Random delays to simulate human behavior

3. **Message Content**
   - ✅ HTTPS links only (automatic conversion)
   - ✅ Option to avoid unsolicited links in first message

4. **Spam Prevention**
   - ✅ STOP command inclusion option
   - ✅ Campaign settings for personalization control

### ⚠️ To Be Implemented

5. **Response Rate Tracking**
   - Track 30% response rate target
   - Monitor engagement per campaign
   - Postpone contacts with low engagement

6. **Geographic Grouping**
   - Group contacts by region
   - Avoid simultaneous international messaging

### ❌ Not Implemented (User Responsibility)

7. **Number Warming**
   - Use WHAPI's warming tool before campaigns
   - Wait at least 1 day after registration before API use
   - Gradually increase activity over several days

8. **Profile Setup**
   - Add profile picture
   - Add business description
   - Use company logo

## Usage Examples

### Example 1: Create Campaign with WhatsApp Settings

```python
from apps.campaigns.models import Campaign
from apps.campaigns.choices import NotificationChannel

campaign = Campaign.objects.create(
    name="Payment Reminders Q1",
    channel=NotificationChannel.WHATSAPP,
    # WhatsApp best practices settings
    whatsapp_personalize_messages=True,
    whatsapp_include_stop_command=True,
    whatsapp_avoid_unsolicited_links=True,
    whatsapp_target_response_rate=30.0,
)
```

### Example 2: Check Rate Limit Status

```python
from apps.notifications.services import WhatsAppRateLimiter

# Get current status
status = WhatsAppRateLimiter.get_rate_limit_status()
print(f"Messages this minute: {status['current_minute_count']}/{status['max_per_minute']}")
print(f"Active minutes today: {status['daily_active_minutes']}/{status['max_daily_minutes']}")
print(f"Consecutive days: {status['consecutive_days']}/{status['max_consecutive_days']}")
```

### Example 3: Manual Rate Limit Reset (Testing)

```python
from apps.notifications.services import WhatsAppRateLimiter

# Reset daily counters
WhatsAppRateLimiter.reset_daily_counters()

# Reset all counters
WhatsAppRateLimiter.reset_all_counters()
```

## Monitoring and Logs

### Log Messages

The implementation logs important events:

```
INFO: WhatsApp message recorded - Minute: 8/12, Daily minutes: 142/360
WARNING: WhatsApp rate limit reached: Per-minute limit reached (12 messages/minute). Retrying in 45 seconds.
INFO: Typing indicator sent to 51987654321@s.whatsapp.net
INFO: Message sent to 51987654321@s.whatsapp.net via WHAPI
```

### Celery Task Monitoring

Monitor WhatsApp message sending tasks:

```bash
# View task status
celery -A config inspect active

# Monitor rate limit retries
celery -A config events
```

## Configuration

### Required Settings

Add to your Django settings:

```python
# settings/base.py or settings/production.py

# WHAPI Configuration
WHAPI_API_TOKEN = env('WHAPI_API_TOKEN')
WHAPI_API_URL = 'https://gate.whapi.cloud'

# Cache Configuration (required for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),
    }
}
```

### Celery Configuration

Ensure Celery can handle task retries:

```python
# config/celery.py

CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
```

## Testing

### Unit Tests

Test rate limiting functionality:

```python
from django.test import TestCase
from apps.notifications.services import WhatsAppRateLimiter

class WhatsAppRateLimiterTest(TestCase):
    def setUp(self):
        WhatsAppRateLimiter.reset_all_counters()

    def test_per_minute_limit(self):
        # Send 12 messages
        for i in range(12):
            rate_check = WhatsAppRateLimiter.can_send_message()
            self.assertTrue(rate_check['allowed'])
            WhatsAppRateLimiter.record_message_sent()

        # 13th message should be blocked
        rate_check = WhatsAppRateLimiter.can_send_message()
        self.assertFalse(rate_check['allowed'])
        self.assertIn('Per-minute limit', rate_check['reason'])
```

### Integration Tests

Test WhatsApp provider with rate limiting:

```python
from apps.notifications.providers.factory import ProviderFactory
from apps.notifications.choices import NotificationChannel

class WHAPIProviderTest(TestCase):
    def test_send_with_rate_limiting(self):
        provider = ProviderFactory.get_provider(NotificationChannel.WHATSAPP)
        result = provider.send_text_message(
            recipient='+51987654321',
            message='Test message'
        )
        self.assertTrue(result['success'])
```

## Troubleshooting

### Issue: Messages not sending

**Symptoms**: Tasks stuck in pending state

**Solution**: Check rate limit status
```python
from apps.notifications.services import WhatsAppRateLimiter
print(WhatsAppRateLimiter.get_rate_limit_status())
```

### Issue: Account banned despite rate limiting

**Possible causes**:
1. Number not properly warmed up (use WHAPI warming tool)
2. Low response rate from recipients (< 30%)
3. Sending to numbers with no prior interaction
4. Profile not completed (missing picture/description)

**Solution**:
- Review WHAPI warming recommendations
- Monitor response rates per campaign
- Ensure profile is complete

### Issue: Rate limit too restrictive

**Adjustment**: Modify constants in `WhatsAppRateLimiter`:

```python
# apps/notifications/services/whatsapp_rate_limiter.py

class WhatsAppRateLimiter:
    MIN_MESSAGES_PER_MINUTE = 6  # Increase carefully
    MAX_MESSAGES_PER_MINUTE = 12  # Increase carefully
    MAX_DAILY_ACTIVITY_HOURS = 6  # Increase carefully
    MAX_CONSECUTIVE_DAYS = 3  # Increase carefully
```

⚠️ **Warning**: Increasing these limits may increase ban risk. Only modify after reviewing WHAPI guidelines.

## Future Enhancements

1. **Response Rate Tracking**
   - Add webhook to receive message status updates
   - Track read receipts and replies
   - Automatically pause contacts with low engagement

2. **Geographic Grouping**
   - Detect international numbers
   - Schedule regional batches
   - Avoid simultaneous international sends

3. **A/B Testing**
   - Test different message variations
   - Monitor which messages get better response rates
   - Optimize content based on engagement

4. **Dashboard**
   - Real-time rate limit status
   - Campaign performance metrics
   - Response rate visualization

## References

- [WHAPI - How to Not Get Banned](https://support.whapi.cloud/help-desk/blocking/how-to-not-get-banned)
- [WHAPI API Documentation](https://docs.whapi.cloud/)
- [WhatsApp Business Policy](https://www.whatsapp.com/legal/business-policy)

## Support

For issues or questions:
1. Review this documentation
2. Check WHAPI support articles
3. Review application logs
4. Contact development team
