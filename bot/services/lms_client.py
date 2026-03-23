from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


@dataclass
class BackendHealth:
    ok: bool
    detail: str


@dataclass
class LabInfo:
    lab_id: str
    title: str


@dataclass
class TaskPassRate:
    task_name: str
    pass_rate: float
    attempts: int | None


class BackendError(Exception):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class LMSClient:
    """Thin LMS backend client used by handlers."""

    def __init__(
        self, base_url: str, api_key: str, timeout_seconds: float = 10.0
    ) -> None:
        self.base_url = self._normalize_base_url(base_url)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _normalize_base_url(self, raw_base_url: str) -> str:
        clean = raw_base_url.strip()
        if not clean:
            raise BackendError(
                "Backend error: LMS_API_BASE_URL is empty. "
                "Set it in .env.bot.secret and try again."
            )
        if not clean.startswith(("http://", "https://")):
            clean = f"http://{clean}"
        return clean.rstrip("/")

    def _host_hint(self) -> str:
        host = urlparse(self.base_url).netloc or self.base_url
        return host

    def _request_json(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        method: str = "GET",
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = httpx.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            if 500 <= status <= 599:
                raise BackendError(
                    f"Backend error: HTTP {status} {reason}. "
                    "The backend service may be down."
                ) from exc
            raise BackendError(
                f"Backend error: HTTP {status} {reason}. "
                "Check LMS_API_KEY and request parameters."
            ) from exc
        except httpx.ConnectError as exc:
            raise BackendError(
                f"Backend error: connection refused ({self._host_hint()}). "
                "Check that the services are running."
            ) from exc
        except httpx.TimeoutException as exc:
            raise BackendError(
                f"Backend error: request timed out ({self._host_hint()}). "
                "The backend may be overloaded or unavailable."
            ) from exc
        except httpx.HTTPError as exc:
            raise BackendError(f"Backend error: {exc}") from exc

    def _extract_list_payload(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("items", "results", "data", "rows"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    def _pick_first_str(
        self, row: dict[str, Any], keys: tuple[str, ...], default: str = ""
    ) -> str:
        for key in keys:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return default

    def health(self) -> BackendHealth:
        items = self.get_items()
        return BackendHealth(
            ok=True, detail=f"Backend is healthy. {len(items)} items available."
        )

    def get_items(self) -> list[dict[str, Any]]:
        payload = self._request_json("/items/")
        return self._extract_list_payload(payload)

    def get_labs(self) -> list[LabInfo]:
        items = self.get_items()
        labs: list[LabInfo] = []
        seen_ids: set[str] = set()
        for row in items:
            raw_id = self._pick_first_str(row, ("id", "item_id", "slug", "key"), "")
            raw_type = self._pick_first_str(
                row, ("type", "item_type", "kind"), ""
            ).lower()
            if raw_type and raw_type != "lab" and not raw_id.lower().startswith("lab-"):
                continue
            if not raw_id.lower().startswith("lab-"):
                continue
            title = self._pick_first_str(
                row,
                ("title", "name", "display_name", "label", "description"),
                raw_id,
            )
            lab_id = raw_id.lower()
            if lab_id in seen_ids:
                continue
            seen_ids.add(lab_id)
            labs.append(LabInfo(lab_id=lab_id, title=title))
        labs.sort(key=lambda item: item.lab_id)
        return labs

    def get_pass_rates(self, lab_id: str) -> list[TaskPassRate]:
        payload = self._request_json("/analytics/pass-rates", params={"lab": lab_id})
        rows = self._extract_list_payload(payload)
        if not rows and isinstance(payload, dict):
            nested = payload.get("pass_rates")
            if isinstance(nested, list):
                rows = [item for item in nested if isinstance(item, dict)]

        results: list[TaskPassRate] = []
        for row in rows:
            task_name = self._pick_first_str(
                row,
                ("task_name", "task", "name", "title", "label", "task_id"),
                "Unknown task",
            )
            pass_raw = row.get(
                "pass_rate", row.get("rate", row.get("avg_pass_rate", 0.0))
            )
            attempts_raw = row.get(
                "attempts", row.get("attempt_count", row.get("total_attempts"))
            )
            try:
                pass_rate = float(pass_raw)
            except (TypeError, ValueError):
                pass_rate = 0.0
            if pass_rate <= 1:
                pass_rate *= 100.0
            attempts: int | None
            try:
                attempts = int(attempts_raw) if attempts_raw is not None else None
            except (TypeError, ValueError):
                attempts = None
            results.append(
                TaskPassRate(
                    task_name=task_name, pass_rate=pass_rate, attempts=attempts
                )
            )
        return results

    def get_learners(self) -> list[dict[str, Any]]:
        payload = self._request_json("/learners/")
        return self._extract_list_payload(payload)

    def get_scores(self, lab_id: str) -> list[dict[str, Any]]:
        payload = self._request_json("/analytics/scores", params={"lab": lab_id})
        return self._extract_list_payload(payload)

    def get_timeline(self, lab_id: str) -> list[dict[str, Any]]:
        payload = self._request_json("/analytics/timeline", params={"lab": lab_id})
        return self._extract_list_payload(payload)

    def get_groups(self, lab_id: str) -> list[dict[str, Any]]:
        payload = self._request_json("/analytics/groups", params={"lab": lab_id})
        return self._extract_list_payload(payload)

    def get_top_learners(
        self, lab_id: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {"limit": limit}
        if lab_id:
            params["lab"] = lab_id
        payload = self._request_json("/analytics/top-learners", params=params)
        return self._extract_list_payload(payload)

    def get_completion_rate(self, lab_id: str) -> dict[str, Any]:
        payload = self._request_json(
            "/analytics/completion-rate", params={"lab": lab_id}
        )
        if isinstance(payload, dict):
            return payload
        rows = self._extract_list_payload(payload)
        return {"rows": rows}

    def trigger_sync(self) -> dict[str, Any]:
        payload = self._request_json("/pipeline/sync", method="POST", json_body={})
        if isinstance(payload, dict):
            return payload
        return {"result": payload}
