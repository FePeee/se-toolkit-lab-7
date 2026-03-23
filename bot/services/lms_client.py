"""LMS API client with real HTTP calls."""

import httpx


class BackendError(Exception):
    """User-facing error for backend failures.

    Contains a friendly message that includes the actual error details
    for debugging, without raw tracebacks.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    @property
    def user_message(self) -> str:
        """Get the user-friendly error message."""
        return self.message


class LmsClient:
    """Client for the LMS backend API.

    This client wraps HTTP calls to the LMS API with error handling,
    converting raw HTTP errors into user-friendly messages.
    """

    def __init__(self, base_url: str | None, api_key: str | None) -> None:
        """Initialize the LMS client.

        Args:
            base_url: Base URL of the LMS API.
            api_key: API key for authentication.
        """
        self.base_url = self._normalize_url(base_url)
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=10.0)

    def _normalize_url(self, url: str | None) -> str | None:
        """Normalize the base URL by adding http:// if missing."""
        if not url:
            return None
        if url.startswith("localhost"):
            return f"http://{url}"
        if not url.startswith("http://") and not url.startswith("https://"):
            return f"http://{url}"
        return url

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _extract_data(self, response: httpx.Response) -> list | dict:
        """Extract data from response, handling both list and wrapped formats.

        Args:
            response: The HTTP response.

        Returns:
            The data payload (list or dict).
        """
        data = response.json()
        # Handle wrapped responses like {"data": [...], "total": N}
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def get_items(self) -> list[dict]:
        """Get all items (labs and tasks) from the backend.

        Returns:
            List of items.

        Raises:
            BackendError: If the backend is unavailable.
        """
        if not self.base_url:
            raise BackendError("LMS API URL not configured. Check .env.bot.secret.")

        try:
            response = await self._client.get(
                f"{self.base_url}/items/",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return self._extract_data(response)
        except httpx.ConnectError as e:
            raise BackendError(
                f"Backend error: connection refused ({self.base_url}). "
                f"Check that the services are running."
            ) from e
        except httpx.TimeoutException as e:
            raise BackendError(
                f"Backend error: timeout connecting to {self.base_url}. "
                f"The service may be overloaded."
            ) from e
        except httpx.HTTPStatusError as e:
            raise BackendError(
                f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. "
                f"The backend service may be down."
            ) from e
        except httpx.HTTPError as e:
            raise BackendError(
                f"Backend error: {type(e).__name__}. Check the backend configuration."
            ) from e

    async def get_labs(self) -> list[dict]:
        """Get list of available labs.

        Returns:
            List of lab dictionaries with id, name, description.

        Raises:
            BackendError: If the backend is unavailable.
        """
        items = await self.get_items()
        # Filter for labs (type == "lab" or has lab-like structure)
        labs = []
        for item in items:
            if isinstance(item, dict):
                item_type = item.get("type", "").lower()
                if item_type == "lab" or "lab" in item.get("id", "").lower():
                    labs.append(item)
        return labs

    async def get_pass_rates(self, lab_id: str) -> list[dict]:
        """Get pass rates for a specific lab.

        Args:
            lab_id: The lab identifier.

        Returns:
            List of pass rate dictionaries with task name, pass rate, attempts.

        Raises:
            BackendError: If the backend is unavailable.
        """
        if not self.base_url:
            raise BackendError("LMS API URL not configured. Check .env.bot.secret.")

        try:
            response = await self._client.get(
                f"{self.base_url}/analytics/pass-rates",
                params={"lab": lab_id},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return self._extract_data(response)
        except httpx.ConnectError as e:
            raise BackendError(
                f"Backend error: connection refused ({self.base_url}). "
                f"Check that the services are running."
            ) from e
        except httpx.TimeoutException as e:
            raise BackendError(
                f"Backend error: timeout connecting to {self.base_url}. "
                f"The service may be overloaded."
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise BackendError(
                    f"Lab '{lab_id}' not found. Use /labs to see available labs."
                ) from e
            raise BackendError(
                f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. "
                f"The backend service may be down."
            ) from e
        except httpx.HTTPError as e:
            raise BackendError(
                f"Backend error: {type(e).__name__}. Check the backend configuration."
            ) from e

    async def health_check(self) -> dict:
        """Check if the LMS backend is healthy.

        Returns:
            Health status dictionary with status and item count.

        Raises:
            BackendError: If the backend is unavailable.
        """
        items = await self.get_items()
        return {
            "status": "healthy",
            "item_count": len(items),
        }
