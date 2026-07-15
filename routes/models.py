from typing import Any, Dict

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/models")
@router.get("/v1/models")
async def models(request: Request) -> Dict[str, Any]:
    settings = request.app.state.settings
    return {"object": "list", "data": [{"id": model, "object": "model", "owned_by": "upstream", **details} for model, details in settings.upstream_models.items()]}
