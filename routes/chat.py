from typing import Any, AsyncIterator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

import anthropic
from schemas import ChatRequest

router = APIRouter()


def error(status: int, message: str, error_type: str = "invalid_request_error", param: str = None, code: str = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"message": message, "type": error_type, "param": param, "code": code}})


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if body.model not in settings.upstream_models:
        return error(400, f"Model '{body.model}' not found", param="model", code="model_not_found")

    provider = settings.upstream_provider_type
    if provider == "anthropic":
        return _anthropic_chat(body, request, settings)
    elif provider == "openai":
        return _openai_chat(body, request, settings)
    else:
        return _generic_chat(body, request, settings)


async def _anthropic_chat(body: ChatRequest, request: Request, settings: Any) -> JSONResponse:
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


async def _openai_chat(body: ChatRequest, request: Request, settings: Any) -> JSONResponse:
    headers = {"Authorization": f"Bearer {settings.upstream_api_key}", "Content-Type": "application/json"}
    try:
        if body.stream:
            upstream_request = request.app.state.client.build_request("POST", f"{settings.upstream_base_url}/chat/completions", json=body.model_dump(exclude_none=True), headers=headers)
            response = await request.app.state.client.send(upstream_request, stream=True)
        else:
            response = await request.app.state.client.post(f"{settings.upstream_base_url}/chat/completions", json=body.model_dump(exclude_none=True), headers=headers)
    except httpx.TimeoutException:
        return error(504, f"Request to upstream timed out after {settings.request_timeout:g} seconds", "server_error", code="timeout")
    except httpx.HTTPError as exc:
        return error(502, f"Upstream request failed: {exc}", "server_error")

    if response.is_error:
        try:
            upstream = response.json()
            message = upstream.get("error", {}).get("message") or upstream.get("message") or response.text
        except ValueError:
            message = response.text
        kind = "rate_limit_error" if response.status_code == 429 else "server_error" if response.status_code >= 500 else "invalid_request_error"
        status = 502 if response.status_code >= 500 else response.status_code
        if body.stream:
            await response.aclose()
        return error(status, message, kind)

    if body.stream:
        async def generate() -> AsyncIterator[bytes]:
            async for chunk in response.aiter_raw():
                yield chunk
            await response.aclose()
        return StreamingResponse(generate(), media_type="text/event-stream")

    return JSONResponse(content=response.json())


async def _generic_chat(body: ChatRequest, request: Request, settings: Any) -> JSONResponse:
    headers = {"Authorization": f"Bearer {settings.upstream_api_key}", "Content-Type": "application/json"}
    try:
        if body.stream:
            upstream_request = request.app.state.client.build_request("POST", f"{settings.upstream_base_url}/chat/completions", json=body.model_dump(exclude_none=True), headers=headers)
            response = await request.app.state.client.send(upstream_request, stream=True)
        else:
            response = await request.app.state.client.post(f"{settings.upstream_base_url}/chat/completions", json=body.model_dump(exclude_none=True), headers=headers)
    except httpx.TimeoutException:
        return error(504, f"Request to upstream timed out after {settings.request_timeout:g} seconds", "server_error", code="timeout")
    except httpx.HTTPError as exc:
        return error(502, f"Upstream request failed: {exc}", "server_error")

    if response.is_error:
        try:
            upstream = response.json()
            message = upstream.get("error", {}).get("message") or upstream.get("message") or response.text
        except ValueError:
            message = response.text
        kind = "rate_limit_error" if response.status_code == 429 else "server_error" if response.status_code >= 500 else "invalid_request_error"
        status = 502 if response.status_code >= 500 else response.status_code
        if body.stream:
            await response.aclose()
        return error(status, message, kind)

    if body.stream:
        async def generate() -> AsyncIterator[bytes]:
            async for chunk in response.aiter_raw():
                yield chunk
            await response.aclose()
        return StreamingResponse(generate(), media_type="text/event-stream")

    return JSONResponse(content=response.json())
