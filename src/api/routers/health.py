"""
Endpoints de verificação de integridade (Health Check).
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from src.api.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificação de integridade",
    description="Retorna o status operacional da API, versão e timestamp corrente.",
)
@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    include_in_schema=False,
)
def check_health() -> HealthResponse:
    now_iso = datetime.now(timezone.utc).isoformat()
    return HealthResponse(
        status="ok",
        app="OmniCrop AI REST API",
        version="1.0.0",
        timestamp=now_iso,
    )
