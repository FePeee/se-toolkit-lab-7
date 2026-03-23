"""LLM API client for intent recognition."""

import httpx


class LlmClient:
    """Client for the LLM API.

    This client wraps HTTP calls to the LLM API for intent recognition.
    Currently provides stub implementations - real API calls will be
    added in Task 3.
    """

    def __init__(
        self,
        base_url: str | None,
        api_key: str | None,
        model: str = "coder-model",
    ) -> None:
        """Initialize the LLM client.

        Args:
            base_url: Base URL of the LLM API.
            api_key: API key for authentication.
            model: Model name to use.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def recognize_intent(self, text: str) -> str:
        """Recognize user intent from text.

        Args:
            text: User's input text.

        Returns:
            Recognized intent (e.g., 'start', 'help', 'health', 'labs', 'scores').
        """
        # Placeholder - will be implemented in Task 3
        # For now, return a default intent
        return "unknown"

    async def chat(self, text: str, context: list[dict] | None = None) -> str:
        """Send a chat message to the LLM.

        Args:
            text: User's message.
            context: Conversation context (message history).

        Returns:
            LLM response text.
        """
        # Placeholder - will be implemented in Task 3
        return "Sorry, I can't process your request yet. Please use commands like /help or /start."
