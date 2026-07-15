# Development

- Use `.venv/bin/python`; do not use the global Python environment.
- Install dependencies with `make install` and validate changes with `make check`.
- Keep `.env` untracked. Update `.env copy.example` when configuration changes.
- `main.py` owns app and router registration.
- `routes/health.py` owns the health endpoint.
- `routes/models.py` owns the model listing endpoint.
- `routes/anthropic.py` owns the Anthropic Messages API (`/messages`, `/v1/messages`), including streaming.
- `routes/chat.py` owns the OpenAI-compatible chat completions endpoint (`/chat/completions`, `/v1/chat/completions`), dispatching to `_anthropic_chat`, `_openai_chat`, or `_generic_chat` based on `upstream_provider_type`. `_generic_chat` is a passthrough for other providers.
- `schemas.py` owns request schemas.
- `config.py` owns settings.
- `anthropic.py` owns Anthropic payload/header translation and SSE-to-OpenAI stream conversion.
- Do not add dependencies unless required.
