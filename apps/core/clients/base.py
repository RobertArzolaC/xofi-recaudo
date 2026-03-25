import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import requests
from django.core.cache import cache

from apps.core.clients.exceptions import (
    APIClientError,
    APIConnectionError,
    APIRateLimitError,
    APITimeoutError,
)

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """
    Base class for all external API clients.

    Provides:
    - Retry logic with exponential backoff
    - Centralized logging
    - Rate limiting
    - Timeout configuration
    - Error handling
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize base API client.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        # Set default headers
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST/PUT)
            params: URL query parameters
            headers: Additional headers
            **kwargs: Additional arguments passed to requests

        Returns:
            dict: Response JSON data

        Raises:
            APIConnectionError: If connection fails
            APITimeoutError: If request times out
            APIRateLimitError: If rate limit is exceeded
            APIClientError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Merge custom headers with session headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        retry_count = 0
        last_exception = None

        while retry_count <= self.max_retries:
            try:
                logger.info(
                    f"Making {method} request to {url} (attempt {retry_count + 1}/{self.max_retries + 1})"
                )

                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers,
                    timeout=self.timeout,
                    **kwargs,
                )

                # Handle response
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(
                        f"Request successful: {method} {url} - Status {response.status_code}"
                    )
                    return response.json() if response.content else {}

                # Check if we should retry
                if self._should_retry(response):
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        wait_time = 2**retry_count  # Exponential backoff: 2s, 4s, 8s
                        logger.warning(
                            f"Request failed with status {response.status_code}, "
                            f"retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        continue

                # Handle specific error cases
                self._handle_error(response)

            except requests.exceptions.Timeout as exc:
                last_exception = exc
                logger.error(f"Request timeout: {method} {url}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = 2**retry_count
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise APITimeoutError(
                    f"Request timed out after {self.timeout}s"
                ) from exc

            except requests.exceptions.ConnectionError as exc:
                last_exception = exc
                logger.error(f"Connection error: {method} {url}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = 2**retry_count
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise APIConnectionError("Failed to connect to API") from exc

            except requests.exceptions.RequestException as exc:
                logger.error(f"Request exception: {method} {url} - {exc}")
                raise APIClientError(f"Request failed: {exc}") from exc

        # If we exhausted retries
        if last_exception:
            if isinstance(last_exception, requests.exceptions.Timeout):
                raise APITimeoutError(
                    f"Request timed out after {self.max_retries} retries"
                )
            raise APIConnectionError(
                f"Connection failed after {self.max_retries} retries"
            )

        raise APIClientError("Request failed after all retry attempts")

    def _handle_error(self, response: requests.Response) -> None:
        """
        Handle HTTP error responses.

        Args:
            response: HTTP response object

        Raises:
            APIRateLimitError: If rate limit exceeded (429)
            APIClientError: For other error statuses
        """
        if response.status_code == 429:
            logger.error(f"Rate limit exceeded: {response.url}")
            raise APIRateLimitError("API rate limit exceeded", status_code=429)

        if response.status_code >= 400 and response.status_code < 500:
            error_message = f"Client error {response.status_code}"
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get(
                    "message", error_message
                )
            except Exception:
                error_message = response.text or error_message

            logger.error(f"Client error: {response.status_code} - {error_message}")
            raise APIClientError(error_message, status_code=response.status_code)

        if response.status_code >= 500:
            error_message = f"Server error {response.status_code}"
            logger.error(f"Server error: {response.status_code} - {response.text}")
            raise APIClientError(error_message, status_code=response.status_code)

    def _should_retry(self, response: requests.Response) -> bool:
        """
        Determine if request should be retried based on status code.

        Args:
            response: HTTP response object

        Returns:
            bool: True if request should be retried
        """
        # Retry on server errors (5xx) and rate limit (429)
        return response.status_code >= 500 or response.status_code == 429

    def health_check(self) -> bool:
        """
        Perform health check on the API.

        Returns:
            bool: True if API is healthy

        Note:
            Subclasses should override this method with specific health check logic.
        """
        try:
            # Default implementation - subclasses should override
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def is_rate_limited(
        self, identifier: str, limit: int = 60, window: int = 60
    ) -> bool:
        """
        Check if request should be rate limited.

        Args:
            identifier: Unique identifier for rate limiting (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds

        Returns:
            bool: True if rate limit exceeded
        """
        cache_key = f"rate_limit:{self.__class__.__name__}:{identifier}"
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            logger.warning(
                f"Rate limit exceeded for {identifier}: {current_count}/{limit} in {window}s"
            )
            return True

        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        return False

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Validate API key is working.

        Returns:
            bool: True if API key is valid

        Note:
            Subclasses must implement this method.
        """
        pass

    def __enter__(self) -> "BaseAPIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close session."""
        _ = exc_type, exc_val, exc_tb  # Mark as used
        self.session.close()
