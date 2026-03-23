"""LMS API client."""

import httpx


class LmsClient:
    """Client for the LMS backend API.

    This client wraps HTTP calls to the LMS API with error handling.
    Currently provides stub implementations - real API calls will be
    added in Task 2.
    """

    def __init__(self, base_url: str | None, api_key: str | None) -> None:
        """Initialize the LMS client.

        Args:
            base_url: Base URL of the LMS API.
            api_key: API key for authentication.
        """
        self.base_url = base_url
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def health_check(self) -> dict:
        """Check if the LMS backend is healthy.

        Returns:
            Health status dictionary.
        """
        # Placeholder - will be implemented in Task 2
        if self.base_url:
            return {"status": "connected", "url": self.base_url}
        return {"status": "not_configured"}

    async def get_labs(self) -> list[dict]:
        """Get list of available labs.

        Returns:
            List of lab dictionaries.
        """
        # Placeholder - will be implemented in Task 2
        return []

    async def get_scores(self, lab_id: str) -> dict:
        """Get scores for a specific lab.

        Args:
            lab_id: The lab identifier.

        Returns:
            Scores dictionary.
        """
        # Placeholder - will be implemented in Task 2
        return {"lab_id": lab_id, "scores": {}}
