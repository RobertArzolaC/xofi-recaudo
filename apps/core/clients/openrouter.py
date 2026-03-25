import logging
from typing import Any

from decouple import config

from apps.core.clients.base import BaseAPIClient
from apps.core.clients.exceptions import APIClientError, APIValidationError

logger = logging.getLogger(__name__)


class OpenRouterClient(BaseAPIClient):
    """
    OpenRouter API client for LLM chat completions.

    Supports:
    - Chat completion with system/user/assistant messages
    - Streaming responses (optional)
    - Token usage tracking
    - Model selection
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to settings)
            model: LLM model to use (defaults to settings)
            base_url: API base URL (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        self.model = model or config(
            "OPENROUTER_MODEL", default="deepseek/deepseek-r1-0528:free"
        )

        base_url = base_url or config(
            "OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"
        )
        api_key = api_key or config("OPENROUTER_API_KEY", default="")
        timeout = timeout or config("OPENROUTER_TIMEOUT", default=30, cast=int)
        max_retries = max_retries or config(
            "OPENROUTER_MAX_RETRIES", default=3, cast=int
        )

        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Set OpenRouter-specific headers
        self.session.headers.update(
            {
                "HTTP-Referer": config("SITE_URL", default="http://localhost:8000"),
                "X-Title": config("SITE_NAME", default="Xara AI Sales Platform"),
            }
        )

        # Track token usage
        self.last_token_usage: dict[str, int] = {}

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate chat completion using OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                Content can be a string or a list of content parts for
                multimodal requests (e.g. vision with image_url).
                Example: [{"role": "user", "content": "..."}]
                Vision:  [{"role": "user", "content": [{"type": "text", ...}, {"type": "image_url", ...}]}]
            temperature: Sampling temperature (0.0 to 2.0, default: 0.7)
            max_tokens: Maximum tokens in response (default: 1000)
            model: Override default model for this request
            **kwargs: Additional parameters passed to API

        Returns:
            str: Generated text response

        Raises:
            APIValidationError: If messages format is invalid
            APIClientError: If API request fails
        """
        # Validate messages
        if not messages:
            raise APIValidationError("Messages list cannot be empty")

        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise APIValidationError(
                    "Each message must have 'role' and 'content' keys"
                )
            if msg["role"] not in ["system", "user", "assistant"]:
                raise APIValidationError(
                    f"Invalid role '{msg['role']}'. Must be 'system', 'user', or 'assistant'"
                )
            content = msg["content"]
            if not isinstance(content, (str, list)):
                raise APIValidationError(
                    "Message 'content' must be a string or a list of content parts"
                )

        # Prepare request payload
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        logger.info(
            f"Sending chat completion request: model={payload['model']}, "
            f"messages={len(messages)}, temperature={temperature}"
        )

        try:
            # Make API request
            response_data = self._make_request(
                method="POST",
                endpoint="/chat/completions",
                data=payload,
            )

            # Extract response text
            if "choices" not in response_data or not response_data["choices"]:
                raise APIClientError("Invalid response format: missing 'choices'")

            choice = response_data["choices"][0]
            if "message" not in choice or "content" not in choice["message"]:
                raise APIClientError("Invalid response format: missing message content")

            response_text = choice["message"].get("content") or choice["message"].get("reasoning") or ""
            if not response_text:
                raise APIClientError("LLM returned empty content")

            # Track token usage
            if "usage" in response_data:
                self.last_token_usage = response_data["usage"]
                logger.info(
                    f"Token usage - Prompt: {self.last_token_usage.get('prompt_tokens', 0)}, "
                    f"Completion: {self.last_token_usage.get('completion_tokens', 0)}, "
                    f"Total: {self.last_token_usage.get('total_tokens', 0)}"
                )

            logger.info(f"Chat completion successful: {len(response_text)} characters")
            return response_text

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat_completion: {e}")
            raise APIClientError(f"Chat completion failed: {e}") from e

    def get_embeddings(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """
        Generate embedding vectors for a list of texts.

        Uses the OpenAI-compatible /embeddings endpoint routed through OpenRouter.

        Args:
            texts: List of strings to embed. Each becomes one vector.
            model: Embedding model to use (defaults to OPENROUTER_EMBEDDING_MODEL env var).

        Returns:
            list: One float vector per input text.

        Raises:
            APIClientError: If the embedding request fails.
        """
        embedding_model = model or config(
            "OPENROUTER_EMBEDDING_MODEL",
            default="openai/text-embedding-3-small",
        )

        payload = {"model": embedding_model, "input": texts}

        logger.info(
            "Requesting embeddings: model=%s, texts=%d", embedding_model, len(texts)
        )

        try:
            response_data = self._make_request(
                method="POST",
                endpoint="/embeddings",
                data=payload,
            )

            if "data" not in response_data:
                raise APIClientError("Embeddings response missing 'data' field")

            # Sort by index to preserve order
            items = sorted(response_data["data"], key=lambda x: x.get("index", 0))
            vectors = [item["embedding"] for item in items]

            logger.info("Embeddings generated: %d vectors", len(vectors))
            return vectors

        except APIClientError:
            raise
        except Exception as e:
            logger.error("Unexpected error generating embeddings: %s", e)
            raise APIClientError(f"Embeddings request failed: {e}") from e

    def get_token_usage(self) -> dict[str, int]:
        """
        Get token usage from last completion request.

        Returns:
            dict: Token usage statistics with keys:
                - prompt_tokens: Tokens in the prompt
                - completion_tokens: Tokens in the completion
                - total_tokens: Total tokens used
        """
        return self.last_token_usage.copy()

    def validate_api_key(self) -> bool:
        """
        Validate OpenRouter API key by making a test request.

        Returns:
            bool: True if API key is valid

        Raises:
            APIClientError: If API key validation fails
        """
        if not self.api_key:
            logger.error("No API key configured")
            return False

        try:
            # Make a minimal test request
            test_messages = [{"role": "user", "content": "test"}]

            self.chat_completion(
                messages=test_messages,
                max_tokens=5,
                temperature=0,
            )

            logger.info("API key validation successful")
            return True

        except APIClientError as e:
            logger.error(f"API key validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during API key validation: {e}")
            return False

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available models from OpenRouter.

        Returns:
            list: List of available models with metadata

        Raises:
            APIClientError: If request fails
        """
        try:
            response_data = self._make_request(method="GET", endpoint="/models")

            if "data" not in response_data:
                raise APIClientError("Invalid response format: missing 'data'")

            models = response_data["data"]
            logger.info(f"Retrieved {len(models)} available models")
            return models

        except APIClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing models: {e}")
            raise APIClientError(f"Failed to list models: {e}") from e

    def health_check(self) -> bool:
        """
        Check if OpenRouter API is healthy.

        Returns:
            bool: True if API is accessible
        """
        try:
            # Try to list models as a health check
            self.list_models()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
