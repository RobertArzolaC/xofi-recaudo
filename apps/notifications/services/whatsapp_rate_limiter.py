import logging
import random
from datetime import datetime, timedelta
from typing import Dict

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class WhatsAppRateLimiter:
    """Service to manage WhatsApp message sending rate limits."""

    # Rate limiting constants based on WHAPI recommendations
    MIN_MESSAGES_PER_MINUTE = 6
    MAX_MESSAGES_PER_MINUTE = 12
    MAX_DAILY_ACTIVITY_HOURS = 6
    MAX_CONSECUTIVE_DAYS = 3

    # Cache key patterns
    CACHE_KEY_MINUTE_COUNT = "whatsapp:rate:minute:{}"
    CACHE_KEY_DAILY_MINUTES = "whatsapp:rate:daily:{}"
    CACHE_KEY_CONSECUTIVE_DAYS = "whatsapp:rate:consecutive_days"
    CACHE_KEY_LAST_MESSAGE_TIME = "whatsapp:rate:last_message"

    # Time constants
    MINUTE_TTL = 60  # 1 minute
    DAILY_TTL = 86400  # 24 hours

    @classmethod
    def can_send_message(cls) -> Dict[str, any]:
        """
        Check if a message can be sent based on rate limits.

        Returns:
            dict: {
                "allowed": bool,
                "reason": str (if not allowed),
                "wait_seconds": int (if not allowed)
            }
        """
        now = timezone.now()
        current_minute = cls._get_minute_key(now)
        current_day = cls._get_day_key(now)

        # Check per-minute limit
        minute_count = cache.get(
            cls.CACHE_KEY_MINUTE_COUNT.format(current_minute), 0
        )
        if minute_count >= cls.MAX_MESSAGES_PER_MINUTE:
            wait_seconds = 60 - now.second
            return {
                "allowed": False,
                "reason": f"Per-minute limit reached ({cls.MAX_MESSAGES_PER_MINUTE} messages/minute)",
                "wait_seconds": wait_seconds,
            }

        # Check daily activity hours
        daily_minutes = cache.get(
            cls.CACHE_KEY_DAILY_MINUTES.format(current_day), set()
        )
        if len(daily_minutes) >= cls.MAX_DAILY_ACTIVITY_HOURS * 60:
            return {
                "allowed": False,
                "reason": f"Daily activity limit reached ({cls.MAX_DAILY_ACTIVITY_HOURS} hours)",
                "wait_seconds": cls._seconds_until_next_day(now),
            }

        # Check consecutive days limit
        consecutive_days = cache.get(cls.CACHE_KEY_CONSECUTIVE_DAYS, 0)
        if consecutive_days >= cls.MAX_CONSECUTIVE_DAYS:
            last_active_day = cache.get(
                f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day"
            )
            if last_active_day and cls._get_day_key(now) == last_active_day:
                return {
                    "allowed": False,
                    "reason": f"Maximum consecutive days reached ({cls.MAX_CONSECUTIVE_DAYS} days)",
                    "wait_seconds": cls._seconds_until_next_day(now),
                }

        return {"allowed": True}

    @classmethod
    def record_message_sent(cls) -> None:
        """Record that a message was sent and update rate limit counters."""
        now = timezone.now()
        current_minute = cls._get_minute_key(now)
        current_day = cls._get_day_key(now)

        # Increment per-minute counter
        minute_key = cls.CACHE_KEY_MINUTE_COUNT.format(current_minute)
        current_count = cache.get(minute_key, 0)
        cache.set(minute_key, current_count + 1, cls.MINUTE_TTL)

        # Add minute to daily activity set
        daily_key = cls.CACHE_KEY_DAILY_MINUTES.format(current_day)
        daily_minutes = cache.get(daily_key, set())
        if not isinstance(daily_minutes, set):
            daily_minutes = set()
        daily_minutes.add(current_minute)
        cache.set(daily_key, daily_minutes, cls.DAILY_TTL)

        # Update consecutive days counter
        cls._update_consecutive_days(current_day)

        # Record last message time
        cache.set(
            cls.CACHE_KEY_LAST_MESSAGE_TIME, now.isoformat(), cls.DAILY_TTL
        )

        logger.info(
            f"WhatsApp message recorded - Minute: {current_count + 1}/{cls.MAX_MESSAGES_PER_MINUTE}, "
            f"Daily minutes: {len(daily_minutes)}/{cls.MAX_DAILY_ACTIVITY_HOURS * 60}"
        )

    @classmethod
    def get_random_delay(cls) -> int:
        """
        Get a randomized delay between messages to avoid patterns.

        Returns:
            int: Delay in seconds (between 5 and 10 seconds)
        """
        return random.randint(5, 10)

    @classmethod
    def get_rate_limit_status(cls) -> Dict[str, any]:
        """
        Get current rate limit status.

        Returns:
            dict: Current rate limit statistics
        """
        now = timezone.now()
        current_minute = cls._get_minute_key(now)
        current_day = cls._get_day_key(now)

        minute_count = cache.get(
            cls.CACHE_KEY_MINUTE_COUNT.format(current_minute), 0
        )
        daily_minutes = cache.get(
            cls.CACHE_KEY_DAILY_MINUTES.format(current_day), set()
        )
        consecutive_days = cache.get(cls.CACHE_KEY_CONSECUTIVE_DAYS, 0)
        last_message_time = cache.get(cls.CACHE_KEY_LAST_MESSAGE_TIME)

        return {
            "current_minute_count": minute_count,
            "max_per_minute": cls.MAX_MESSAGES_PER_MINUTE,
            "daily_active_minutes": len(daily_minutes)
            if isinstance(daily_minutes, set)
            else 0,
            "max_daily_minutes": cls.MAX_DAILY_ACTIVITY_HOURS * 60,
            "consecutive_days": consecutive_days,
            "max_consecutive_days": cls.MAX_CONSECUTIVE_DAYS,
            "last_message_time": last_message_time,
        }

    @classmethod
    def reset_daily_counters(cls) -> None:
        """Reset daily counters (for testing or manual intervention)."""
        now = timezone.now()
        current_day = cls._get_day_key(now)
        cache.delete(cls.CACHE_KEY_DAILY_MINUTES.format(current_day))
        logger.info("Daily WhatsApp counters reset")

    @classmethod
    def reset_all_counters(cls) -> None:
        """Reset all counters (for testing or manual intervention)."""
        cache.delete(cls.CACHE_KEY_CONSECUTIVE_DAYS)
        cache.delete(f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day")
        cache.delete(cls.CACHE_KEY_LAST_MESSAGE_TIME)
        cls.reset_daily_counters()
        logger.info("All WhatsApp rate limit counters reset")

    @classmethod
    def _get_minute_key(cls, dt: datetime) -> str:
        """Get cache key for current minute."""
        return dt.strftime("%Y%m%d%H%M")

    @classmethod
    def _get_day_key(cls, dt: datetime) -> str:
        """Get cache key for current day."""
        return dt.strftime("%Y%m%d")

    @classmethod
    def _seconds_until_next_day(cls, now: datetime) -> int:
        """Calculate seconds until next day."""
        next_day = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return int((next_day - now).total_seconds())

    @classmethod
    def _update_consecutive_days(cls, current_day: str) -> None:
        """Update consecutive days counter."""
        last_day = cache.get(f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day")
        consecutive_days = cache.get(cls.CACHE_KEY_CONSECUTIVE_DAYS, 0)

        if not last_day:
            # First day
            cache.set(cls.CACHE_KEY_CONSECUTIVE_DAYS, 1, cls.DAILY_TTL * 7)
            cache.set(
                f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day",
                current_day,
                cls.DAILY_TTL * 7,
            )
        else:
            # Check if it's a consecutive day
            last_date = datetime.strptime(last_day, "%Y%m%d").date()
            current_date = datetime.strptime(current_day, "%Y%m%d").date()
            days_diff = (current_date - last_date).days

            if days_diff == 1:
                # Consecutive day
                consecutive_days += 1
                cache.set(
                    cls.CACHE_KEY_CONSECUTIVE_DAYS,
                    consecutive_days,
                    cls.DAILY_TTL * 7,
                )
                cache.set(
                    f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day",
                    current_day,
                    cls.DAILY_TTL * 7,
                )
            elif days_diff > 1:
                # Reset counter - there was a break
                cache.set(cls.CACHE_KEY_CONSECUTIVE_DAYS, 1, cls.DAILY_TTL * 7)
                cache.set(
                    f"{cls.CACHE_KEY_CONSECUTIVE_DAYS}:last_day",
                    current_day,
                    cls.DAILY_TTL * 7,
                )
            # If days_diff == 0, we're still on the same day, no need to update
