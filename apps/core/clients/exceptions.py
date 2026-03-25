class APIClientError(Exception):
    """Base exception for all API client errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """
        Initialize API client error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIConnectionError(APIClientError):
    """Raised when connection to API fails."""

    pass


class APITimeoutError(APIClientError):
    """Raised when API request times out."""

    pass


class APIRateLimitError(APIClientError):
    """Raised when API rate limit is exceeded."""

    pass


class APIValidationError(APIClientError):
    """Raised when API request validation fails."""

    pass
