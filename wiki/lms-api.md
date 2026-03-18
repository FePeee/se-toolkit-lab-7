# LMS API

## About the LMS API

## LMS API port

### `<lms-api-port>` placeholder

## `Caddy`

### `Caddyfile` in this project

In this project, the [`Caddyfile`](./caddy.md#caddyfile) is at [`caddy/Caddyfile`](../caddy/Caddyfile).

This configuration:

- Reads the value of [`CADDY_CONTAINER_PORT`](./dotenv-docker-secret.md#caddy_container_port) in [`.env.docker.secret`](./dotenv-docker-secret.md#what-is-envdockersecret).
- Makes `Caddy` [listen on the port](./computer-networks.md#listen-on-a-port) listen on this port inside a [`Docker` container](./docker.md#container).
- [Serves frontend files](#caddy-serves-frontend-files)
- [Forwards requests to backend](#caddy-forwards-requests-to-backend)

### `Caddy` serves frontend files

`Caddy` serves static front-end files from `/srv` for all other paths.

The `try_files` directive falls back to `index.html` for client-side routing.

### `Caddy` forwards requests to backend

`Caddy` routes [API endpoints](./web-api.md#endpoint) (`/items*`, `/learners*`, `/interactions*`, `/docs*`, `/openapi.json`) to the [`app` service](./docker-compose-yml.md#app-service).
