from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator, Dict


def payload(request: Any) -> Dict[str, Any]:
    system = [message.content for message in request.messages if message.role == "system"]
    result: Dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "messages": [message.model_dump() for message in request.messages if message.role != "system"],
    }
    if system:
        result["system"] = "\n\n".join(item for item in system if isinstance(item, str))
    if request.temperature is not None:
        result["temperature"] = request.temperature
    if request.top_p is not None:
        result["top_p"] = request.top_p
    if request.stop:
        result["stop_sequences"] = [request.stop] if isinstance(request.stop, str) else request.stop
    return result


def headers(api_key: str) -> Dict[str, str]:
    return {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}


def openai_response(data: Dict[str, Any], model: str) -> Dict[str, Any]:
    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    usage = data.get("usage", {})
    prompt_tokens = usage.get("input_tokens", 0)
    completion_tokens = usage.get("output_tokens", 0)
    finish_reason = {"end_turn": "stop", "max_tokens": "length"}.get(data.get("stop_reason"), "stop")
    return {
        "id": f"chatcmpl-{data.get('id', uuid.uuid4().hex)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get("model", model),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens},
    }


async def openai_stream(lines: AsyncIterator[str], model: str) -> AsyncIterator[str]:
    response_id = ""
    response_model = model
    created = int(time.time())
    async for line in lines:
        if not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type == "message_start":
            message = event.get("message", {})
            response_id = message.get("id", uuid.uuid4().hex)
            response_model = message.get("model", model)
            chunk = {"id": "chatcmpl-{}".format(response_id), "object": "chat.completion.chunk", "created": created, "model": response_model, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]}
        elif event_type == "content_block_delta" and event.get("delta", {}).get("type") == "text_delta":
            chunk = {"id": "chatcmpl-{}".format(response_id), "object": "chat.completion.chunk", "created": created, "model": response_model, "choices": [{"index": 0, "delta": {"content": event["delta"].get("text", "")}, "finish_reason": None}]}
        elif event_type == "message_delta":
            reason = {"end_turn": "stop", "max_tokens": "length"}.get(event.get("delta", {}).get("stop_reason"), "stop")
            chunk = {"id": "chatcmpl-{}".format(response_id), "object": "chat.completion.chunk", "created": created, "model": response_model, "choices": [{"index": 0, "delta": {}, "finish_reason": reason}]}
        else:
            continue
        yield "data: {}\n\n".format(json.dumps(chunk))
    yield "data: [DONE]\n\n"
