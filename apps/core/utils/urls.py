from typing import Optional
from constance import config


def get_absolute_url(path: str) -> str:
    """
    Ensure a path is turned into an absolute URL using config.COMPANY_DOMAIN.

    Guarantees a protocol (https) is present and avoids double slashes
    between domain and path.

    Args:
        path: Relative URL path (e.g. '/media/file.jpg')

    Returns:
        str: Absolute URL (e.g. 'https://xofi.com/media/file.jpg')
    """
    domain = config.COMPANY_DOMAIN.rstrip("/")
    if not domain.startswith(("http://", "https://")):
        domain = f"https://{domain}"

    if not path.startswith("/"):
        path = f"/{path}"

    return f"{domain}{path}"
