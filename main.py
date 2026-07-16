from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import time

import httpx
from fastapi import FastAPI, Request


def configure_logging() -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for name, filename, level in (("access", "access.log", logging.INFO), ("error", "error.log", logging.ERROR)):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = RotatingFileHandler(filename, maxBytes=10_000_000, backupCount=3)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


configure_logging()
access_log = logging.getLogger("access")
error_log = logging.getLogger("error")

from config import Settings
from routes import health, models, anthropic, chat


async def log_upstream_response(response: httpx.Response) -> None:
    logger = error_log if response.is_error else access_log
    logger.log(logging.ERROR if response.is_error else logging.INFO, "upstream method=%s url=%s status=%s", response.request.method, response.url, response.status_code)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.client = httpx.AsyncClient(timeout=settings.request_timeout, event_hooks={"response": [log_upstream_response]})
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_access(request: Request, call_next):
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        error_log.exception("request_failed method=%s path=%s", request.method, request.url.path)
        raise
    access_log.info("method=%s path=%s status=%s duration_ms=%d", request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000)
    return response


app.include_router(health.router)
app.include_router(models.router)
app.include_router(anthropic.router)
app.include_router(chat.router)
