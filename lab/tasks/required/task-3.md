# Intent-Based Natural Language Routing

Slash commands work, but real users don't think in `/commands` — they ask questions like "which lab has the worst results?" In this task, you add an LLM-powered intent router: the user types plain text, and the bot figures out what data to fetch and how to answer.

This builds on Lab 6 — same tool use pattern (give the LLM tools, let it decide), but now embedded in a user-facing product instead of a CLI.

## Requirements targeted

- **P1.1** Natural language intent routing — plain text interpreted by LLM
- **P1.2** All 9 backend endpoints wrapped as LLM tools
- **P1.3** Inline keyboard buttons
- **P1.4** Multi-step reasoning (chaining API calls)

## What you will build

An intent router: user message → LLM with tool definitions → API calls → formatted response.

```terminal
$ uv run bot.py --test "which lab has the lowest pass rate?"
Based on the data, Lab 03 has the lowest average pass rate at 62.3%.
- Backend API: 58.1% (145 attempts)
- Security Hardening: 66.5% (132 attempts)
```

## How it works

```
User: "which lab has the worst results?"
  → bot sends message + tool definitions to LLM
  → LLM decides: call get_pass_rates for each lab
  → bot executes the API calls
  → feeds results back to LLM
  → LLM summarizes
  → bot sends response
```

The LLM receives the user's message, a list of tools (your backend endpoints as function schemas), and a system prompt. It responds with tool calls. Your bot executes them, feeds results back, and the LLM produces the final answer.

## Required tools

Define all 9 backend endpoints as LLM tools — this gives the router enough variety for diverse questions:

| Tool | Endpoint | LLM description |
|------|----------|----------------|
| `get_items` | `GET /items/` | List of labs and tasks |
| `get_learners` | `GET /learners/` | Enrolled students and groups |
| `get_scores` | `GET /analytics/scores?lab=` | Score distribution (4 buckets) |
| `get_pass_rates` | `GET /analytics/pass-rates?lab=` | Per-task averages and attempt counts |
| `get_timeline` | `GET /analytics/timeline?lab=` | Submissions per day |
| `get_groups` | `GET /analytics/groups?lab=` | Per-group scores and student counts |
| `get_top_learners` | `GET /analytics/top-learners?lab=&limit=` | Top N learners by score |
| `get_completion_rate` | `GET /analytics/completion-rate?lab=` | Completion rate percentage |
| `trigger_sync` | `POST /pipeline/sync` | Refresh data from autochecker |

Example tool schema:

```python
{
    "type": "function",
    "function": {
        "name": "get_pass_rates",
        "description": "Get per-task average scores and attempt counts for a lab",
        "parameters": {
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
            },
            "required": ["lab"],
        },
    },
}
```

## Scenarios

**Single API call:**

| Message | Behavior |
|---------|----------|
| "what labs are available?" | `get_items` → list labs |
| "show me scores for lab 4" | `get_pass_rates(lab="lab-04")` → format |
| "who are the top 5 students?" | `get_top_learners(limit=5)` → leaderboard |
| "which group is best in lab 3?" | `get_groups(lab="lab-03")` → rank |

**Multi-step:**

| Message | Behavior |
|---------|----------|
| "which lab has the lowest pass rate?" | `get_items` → `get_pass_rates` per lab → compare |
| "compare group A and group B" | `get_groups` → filter → compare |

**Fallback:**

| Message | Behavior |
|---------|----------|
| "hello" | Greeting + capabilities hint |
| "asdfgh" | "I didn't understand. Here's what I can do..." |
| "lab 4" | "What about lab 4? I can show scores, pass rates..." |

## Inline buttons

Add keyboard buttons so users can discover actions without typing. For example, after `/start` show buttons for common queries.

## Verify

Try these on your VM:

```terminal
cd ~/se-toolkit-lab-7/bot
uv run bot.py --test "what labs are available"
uv run bot.py --test "which lab has the lowest pass rate"
uv run bot.py --test "who are the top 5 students in lab 4"
uv run bot.py --test "asdfgh"
```

The first three should return real answers with data from your backend. The last should return a helpful fallback, not a crash.

## Acceptance criteria

- [ ] `--test "what labs are available"` returns non-empty answer (at least 20 chars).
- [ ] `--test "which lab has the lowest pass rate"` mentions a specific lab.
- [ ] `--test "asdfgh"` returns a helpful message, no crash.
- [ ] Source code contains keyboard/button setup.
- [ ] Source code defines at least 9 tool/function schemas.
- [ ] The LLM decides which tool to call — no regex or keyword matching in the routing path. After the LLM returns tool calls, results are fed back to the LLM for the final answer.
- [ ] Git workflow followed.

