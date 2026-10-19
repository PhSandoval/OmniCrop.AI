"""
Endpoints para Trilha de Auditoria LGPD e Governança de Dados.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import AuthContext, get_auth_context
from src.api.schemas.audit import AuditLogResponse
from src.data.db import get_audit_logs

router = APIRouter()


@router.get(
    "/audit/logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar trilha de auditoria LGPD do usuário",
    description="Retorna o histórico cronológico de ações críticas (alterações de parâmetros, exportação de laudos, exclusões).",
)
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=500, description="Limite de registros retornados"),
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> List[AuditLogResponse]:
    logs_raw = get_audit_logs(user_id=auth_ctx.user_id, limit=limit, access_token=auth_ctx.access_token)
    response: List[AuditLogResponse] = []
    for log in logs_raw:
        response.append(
            AuditLogResponse(
                id=str(log.get("id", "")),
                user_id=str(log.get("user_id", auth_ctx.user_id)),
                farm_id=str(log.get("farm_id")) if log.get("farm_id") else None,
                action=log.get("action", ""),
                entity_type=log.get("entity_type", ""),
                entity_id=str(log.get("entity_id")) if log.get("entity_id") else None,
                details=log.get("details", {}),
                ip_address=log.get("ip_address"),
                trace_id=log.get("trace_id"),
                created_at=log.get("created_at"),
            )
        )
    return response
