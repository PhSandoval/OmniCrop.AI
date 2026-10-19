from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Resposta para checagem de integridade e prontidão da API."""
    status: str = Field(default="ok", description="Status operacional do serviço")
    app: str = Field(default="OmniCrop AI REST API", description="Nome da aplicação")
    version: str = Field(default="1.0.0", description="Versão semântica da API")
    timestamp: str = Field(..., description="Timestamp ISO 8601 da requisição")
    circuit_breakers: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Estado operacional dos Circuit Breakers ativos",
    )


class ErrorResponse(BaseModel):
    """Formato padronizado de erro para a API."""
    detail: str = Field(..., description="Mensagem descritiva do erro")
    error_code: Optional[str] = Field(default=None, description="Código de erro corporativo")
