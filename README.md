# LLM Adapter

FastAPI adapter that exposes OpenAI-compatible chat completion endpoints and forwards requests to Anthropic or OpenAI-compatible upstreams.

## Setup

```sh
python3 -m venv .venv
make install
cp ".env copy.example" .env
```

Edit `.env` with the upstream URL, API key, provider, models, and port.

`UPSTREAM_MODELS` is a JSON object keyed by model ID:

```env
UPSTREAM_MODELS='{"claude-3-5-haiku-20241022":{"name":"Claude 3.5 Haiku (Fast)"}}'
```

## Commands

```sh
make run
make check
make docker-build
make docker-run
```

`make run` loads `.env` and starts the service on `PORT`. The API provides:

- `GET /health` — health check
- `GET /models`, `GET /v1/models` — list available models
- `POST /messages`, `POST /v1/messages` — Anthropic Messages API (streaming supported)
- `POST /chat/completions`, `POST /v1/chat/completions` — OpenAI-compatible (streaming supported)

`n` other than `1` is not supported.
