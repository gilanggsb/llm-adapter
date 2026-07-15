from typing import Dict

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> Dict[str, str]:
    settings = request.app.state.settings
    return {"status": "healthy", "upstream": settings.upstream_base_url, "upstream_type": settings.upstream_provider_type}
