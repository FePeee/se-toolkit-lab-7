# Deploy and Document

The bot works locally via `--test` mode, but it's not a real product until it's running on the VM and responding in Telegram. In this task, you containerize the bot, add it to Docker Compose alongside the backend, and document how to deploy.

## Requirements targeted

- **P3.1** Bot containerized with Dockerfile
- **P3.2** Added as service in `docker-compose.yml`
- **P3.3** Deployed and running on VM
- **P3.4** README documents deployment

## Deliverables

### 1. Bot Dockerfile (`bot/Dockerfile`)

Installs dependencies using `uv sync` from `bot/pyproject.toml` and runs the bot entry point.

> [!IMPORTANT]
> Do **not** use `requirements.txt` or `pip install`. The project uses `uv` and `pyproject.toml` exclusively. Having both `pyproject.toml` and `requirements.txt` leads to dependency drift and random breakage. If your coding agent generates a `requirements.txt`, delete it.

### 2. Bot service in `docker-compose.yml`

Add a `bot` service to the existing compose file:
- Connects to backend via Docker network (service name, not `localhost`)
- Reads `BOT_TOKEN` and LLM credentials from environment
- Restarts unless stopped

> [!IMPORTANT]
> **Qwen proxy networking.** The backend (`app`) is in the same compose file, so the bot reaches it by service name (`http://app:8000`). But the Qwen Code API proxy is a **separate** docker-compose project — it's on a different Docker network. The bot container can't reach it by service name or via `localhost`.
>
> To reach host-mapped ports from inside a container on Linux, use `extra_hosts` with `host.docker.internal`:
>
> ```yaml
> bot:
>   extra_hosts:
>     - "host.docker.internal:host-gateway"
> ```
>
> Then use `http://host.docker.internal:42005/v1` as the LLM API base URL.

### 3. Deployment verification

Bot container runs alongside the backend on your VM. Both are healthy.

### 4. README deploy section

Add a "Deploy" section explaining: required env vars, docker compose commands, how to verify.

## Verify

On your VM:

```terminal
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret up --build -d
docker compose --env-file .env.docker.secret ps
```

You should see the bot service running alongside app, postgres, caddy. Then open Telegram and send `/start` to your bot — it should respond.

## Acceptance criteria

- [ ] Repo deployed at `~/se-toolkit-lab-7` on VM.
- [ ] `git remote get-url origin` matches student's GitHub repo.
- [ ] `docker-compose.yml` includes a bot service.
- [ ] Bot container running (`docker ps` shows it).
- [ ] Backend still healthy (`curl -sf http://localhost:42002/docs` returns 200).
- [ ] README has a section with "deploy" in heading.
- [ ] Bot responds in Telegram (TA-verified).

