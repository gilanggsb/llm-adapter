from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from config import Settings
from routes import health, models, anthropic, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.client = httpx.AsyncClient(timeout=settings.request_timeout)
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)
app.include_router(health.router)
app.include_router(models.router)
app.include_router(anthropic.router)
app.include_router(chat.router)
