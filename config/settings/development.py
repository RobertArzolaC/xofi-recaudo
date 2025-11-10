from celery.schedules import crontab

from config.settings.base import *  # noqa
from config.settings.tools.django_constance import *  # noqa
from config.settings.tools.django_easy_audit import *  # noqa

# Apps settings

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
    "django_browser_reload",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

INTERNAL_IPS = ["localhost", "127.0.0.1"]

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.cache.CachePanel",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    "IS_RUNNING_TESTS": False,
}

DEBUG_TOOLBAR_CONFIG["IS_RUNNING_TESTS"] = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

TAILWIND_DEV_MODE = True

# Celery tasks configuration

CELERY_BEAT_SCHEDULE = {
    "execute_test_task": {
        "task": "apps.core.tasks.test_task",
        "schedule": crontab(hour=22, minute=0),
        "kwargs": {},
    },
    "update-campaign-status": {
        "task": "campaigns.update_campaign_status",
        "schedule": crontab(minute="*/2"),  # Cada 2 minutos
        "options": {
            "expires": 240,  # Expira después de 4 minutos
        },
    },
    "send-scheduled-notifications": {
        "task": "notifications.send_scheduled_notifications",
        "schedule": crontab(minute="*/5"),  # Cada 5 minutos
    },
}
