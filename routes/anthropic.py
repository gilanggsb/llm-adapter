from typing import Any, AsyncIterator, Dict

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

import anthropic
from schemas import ChatRequest

router = APIRouter()


def error(status: int, message: str, error_type: str = "invalid_request_error", param: str = None, code: str = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"message": message, "type": error_type, "param": param, "code": code}})


@router.post("/messages")
@router.post("/v1/messages")
async def anthropic_messages(body: Dict[str, Any], request: Request) -> JSONResponse:
    settings = request.app.state.settings
    model = body.get("model")
    if model not in settings.upstream_models:
        return error(400, f"Model '{model}' not found", param="model", code="model_not_found")

    headers = anthropic.headers(settings.upstream_api_key)
    try:
        if body.get("stream"):
            upstream_request = request.app.state.client.build_request("POST", f"{settings.upstream_base_url}/messages", json=body, headers=headers)
            response = await request.app.state.client.send(upstream_request, stream=True)
        else:
            response = await request.app.state.client.post(f"{settings.upstream_base_url}/messages", json=body, headers=headers)
    except httpx.TimeoutException:
        return error(504, f"Request to upstream timed out after {settings.request_timeout:g} seconds", "server_error", code="timeout")
    except httpx.HTTPError as exc:
        return error(502, f"Upstream request failed: {exc}", "server_error")

    if response.is_error:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        if hasattr(response, "aclose"):
            await response.aclose()
        return error(response.status_code, message)

    if body.get("stream"):
        async def generate() -> AsyncIterator[bytes]:
            async for chunk in response.aiter_lines():
                yield f"{chunk}\n".encode()
            await response.aclose()
        return StreamingResponse(generate(), media_type="text/event-stream")
    return JSONResponse(content=response.json())


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if body.model not in settings.upstream_models:
        return error(400, f"Model '{body.model}' not found", param="model", code="model_not_found")

    payload = anthropic.payload(body)
    if body.stream:
        payload["stream"] = True
    headers = anthropic.headers(settings.upstream_api_key)
    try:
        if body.stream:
            upstream_request = request.app.state.client.build_request("POST", f"{settings.upstream_base_url}/messages", json=payload, headers=headers)
            response = await request.app.state.client.send(upstream_request, stream=True)
        else:
            response = await request.app.state.client.post(f"{settings.upstream_base_url}/messages", json=payload, headers=headers)
    except httpx.TimeoutException:
        return error(504, f"Request to upstream timed out after {settings.request_timeout:g} seconds", "server_error", code="timeout")
    except httpx.HTTPError as exc:
        return error(502, f"Upstream request failed: {exc}", "server_error")

    if response.is_error:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        kind = "rate_limit_error" if response.status_code == 429 else "server_error" if response.status_code >= 500 else "invalid_request_error"
        status = 502 if response.status_code >= 500 else response.status_code
        if body.stream:
            await response.aclose()
        return error(status, message, kind)

    if body.stream:
        async def generate() -> AsyncIterator[bytes]:
            async for chunk in anthropic.openai_stream(response.aiter_lines(), body.model):
                yield chunk.encode()
            await response.aclose()
        return StreamingResponse(generate(), media_type="text/event-stream")

    data = response.json()
    return JSONResponse(content=anthropic.openai_response(data, body.model))
