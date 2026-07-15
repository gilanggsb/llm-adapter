from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: Union[str, List[Dict[str, Any]]]


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage] = Field(min_length=1)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: int = Field(default=1024, gt=0)
    top_p: Optional[float] = Field(default=None, gt=0, le=1)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    n: int = Field(default=1, ge=1)

    @field_validator("n")
    @classmethod
    def one_completion_only(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Only n=1 is supported")
        return value
