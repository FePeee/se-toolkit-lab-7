from __future__ import annotations

import json
import sys
from typing import Any

import httpx

from services.lms_client import BackendError, LMSClient


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        normalized_base = base_url.strip()
        if not normalized_base.startswith(("http://", "https://")):
            normalized_base = f"http://{normalized_base}"
        self.base_url = normalized_base.rstrip("/")
        self.model = model
        self.max_tool_iterations = 10

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_items",
                    "description": "List labs and tasks from LMS backend.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learners",
                    "description": "Get enrolled learners and their groups.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scores",
                    "description": "Get score distribution buckets for a specific lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab id, e.g. lab-01",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pass_rates",
                    "description": "Get per-task pass rates and attempts for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab id, e.g. lab-01",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timeline",
                    "description": "Get submissions per day for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab id, e.g. lab-01",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_groups",
                    "description": "Get per-group performance for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab id, e.g. lab-01",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_learners",
                    "description": "Get top learners by score, optionally scoped to a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Optional lab id, e.g. lab-01",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum learners to return",
                                "default": 5,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_completion_rate",
                    "description": "Get completion rate percentage for a specific lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab id, e.g. lab-01",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_sync",
                    "description": "Trigger LMS ETL sync to refresh analytics data.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def _system_prompt(self) -> str:
        return (
            "You are an LMS analytics assistant. Use tools for factual answers. "
            "When user asks about labs, learners, scores, pass rates, timeline, groups, "
            "completion, or top learners, call the relevant tools first and then summarize. "
            "You may call multiple tools when needed. Prefer concise answers with concrete numbers. "
            "If user message is greeting or gibberish, respond helpfully with capabilities. "
            "Never invent backend data."
        )

    def _chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("LLM returned no choices")
        return choices[0].get("message", {})

    def _as_tool_result(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=True, default=str)

    def _execute_tool(
        self, name: str, arguments: dict[str, Any], lms_client: LMSClient
    ) -> Any:
        if name == "get_items":
            return lms_client.get_items()
        if name == "get_learners":
            return lms_client.get_learners()
        if name == "get_scores":
            return lms_client.get_scores(str(arguments.get("lab", "")))
        if name == "get_pass_rates":
            rows = lms_client.get_pass_rates(str(arguments.get("lab", "")))
            return [
                {
                    "task_name": row.task_name,
                    "pass_rate": row.pass_rate,
                    "attempts": row.attempts,
                }
                for row in rows
            ]
        if name == "get_timeline":
            return lms_client.get_timeline(str(arguments.get("lab", "")))
        if name == "get_groups":
            return lms_client.get_groups(str(arguments.get("lab", "")))
        if name == "get_top_learners":
            lab = arguments.get("lab")
            limit = int(arguments.get("limit", 5))
            return lms_client.get_top_learners(str(lab) if lab else None, limit=limit)
        if name == "get_completion_rate":
            return lms_client.get_completion_rate(str(arguments.get("lab", "")))
        if name == "trigger_sync":
            return lms_client.trigger_sync()
        raise ValueError(f"Unknown tool: {name}")

    def answer(self, text: str, lms_client: LMSClient) -> str:
        tools = self._tools()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": text},
        ]

        try:
            for _ in range(self.max_tool_iterations):
                message = self._chat(messages, tools)
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": message.get("content", ""),
                            "tool_calls": tool_calls,
                        }
                    )
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        name = function.get("name", "")
                        raw_args = function.get("arguments", "{}")
                        try:
                            arguments = (
                                json.loads(raw_args)
                                if isinstance(raw_args, str)
                                else raw_args
                            )
                        except json.JSONDecodeError:
                            arguments = {}
                        print(
                            f"[tool] LLM called: {name}({json.dumps(arguments, ensure_ascii=True)})",
                            file=sys.stderr,
                        )
                        try:
                            result = self._execute_tool(name, arguments, lms_client)
                            result_text = self._as_tool_result(result)
                            if isinstance(result, list):
                                print(
                                    f"[tool] Result: {len(result)} rows",
                                    file=sys.stderr,
                                )
                            else:
                                print("[tool] Result: object", file=sys.stderr)
                        except BackendError as exc:
                            result_text = self._as_tool_result(
                                {"error": exc.user_message}
                            )
                            print(
                                f"[tool] Result: backend error -> {exc.user_message}",
                                file=sys.stderr,
                            )
                        except Exception as exc:  # noqa: BLE001
                            result_text = self._as_tool_result(
                                {"error": f"Tool execution failed: {exc}"}
                            )
                            print(
                                f"[tool] Result: tool failure -> {exc}", file=sys.stderr
                            )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", ""),
                                "name": name,
                                "content": result_text,
                            }
                        )
                    print(
                        f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM",
                        file=sys.stderr,
                    )
                    continue

                content = message.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                return "I could not produce an answer from the available data."
            return "I reached the tool-call limit before finishing. Try a more specific question."
        except httpx.HTTPStatusError as exc:
            return f"LLM error: HTTP {exc.response.status_code} {exc.response.reason_phrase}"
        except httpx.HTTPError as exc:
            return f"LLM error: {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"LLM error: {exc}"
