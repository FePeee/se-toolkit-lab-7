from __future__ import annotations

from services import BackendError, LLMClient, LMSClient


def handle_start() -> str:
    return "Welcome to SE Toolkit Bot.\nUse /help to see available commands."


def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start - show welcome message\n"
        "/help - list available commands\n"
        "/health - check LMS backend status\n"
        "/labs - list available labs\n"
        "/scores <lab-id> - show per-task pass rates for a lab"
    )


def handle_health(lms_client: LMSClient) -> str:
    try:
        health = lms_client.health()
    except BackendError as exc:
        return exc.user_message
    if not health.ok:
        return f"Backend error: {health.detail}"
    return health.detail


def handle_labs(lms_client: LMSClient) -> str:
    try:
        labs = lms_client.get_labs()
    except BackendError as exc:
        return exc.user_message
    if not labs:
        return "No labs found in backend data."
    lines = ["Available labs:"]
    for lab in labs:
        lines.append(f"- {lab.lab_id.upper()} - {lab.title}")
    return "\n".join(lines)


def handle_scores(lab_id: str | None, lms_client: LMSClient) -> str:
    if not lab_id:
        return "Usage: /scores <lab-id>"
    lab_key = lab_id.strip().lower()
    try:
        pass_rates = lms_client.get_pass_rates(lab_key)
    except BackendError as exc:
        return exc.user_message

    if not pass_rates:
        return f"No pass-rate data found for {lab_key}."

    lines = [f"Pass rates for {lab_key.upper()}:"]
    for entry in pass_rates:
        if entry.attempts is None:
            lines.append(f"- {entry.task_name}: {entry.pass_rate:.1f}%")
        else:
            lines.append(
                f"- {entry.task_name}: {entry.pass_rate:.1f}% ({entry.attempts} attempts)"
            )
    return "\n".join(lines)


def handle_free_text(text: str, llm_client: LLMClient, lms_client: LMSClient) -> str:
    return llm_client.answer(text, lms_client)
