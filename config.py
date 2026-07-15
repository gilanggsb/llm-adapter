from __future__ import annotations

import json
import os
from typing import Dict, Literal

from pydantic import BaseModel, Field

ProviderType = Literal["anthropic", "openai"]


class Settings(BaseModel):
    upstream_base_url: str = Field(min_length=1)
    upstream_api_key: str = Field(min_length=1)
    upstream_provider_type: ProviderType
    upstream_models: Dict[str, Dict[str, str]] = Field(min_length=1)
    request_timeout: float = Field(default=60, gt=0)

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            models = json.loads(os.environ["UPSTREAM_MODELS"])
        except (KeyError, json.JSONDecodeError) as error:
            raise RuntimeError("UPSTREAM_MODELS must be a JSON object") from error
        return cls(
            upstream_base_url=os.environ["UPSTREAM_BASE_URL"].rstrip("/"),
            upstream_api_key=os.environ["UPSTREAM_API_KEY"],
            upstream_provider_type=os.environ.get("UPSTREAM_PROVIDER_TYPE", "anthropic"),
            upstream_models=models,
            request_timeout=float(os.environ.get("REQUEST_TIMEOUT", "60")),
        )
