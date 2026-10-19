"""
Schemas Pydantic v2 para Trilha de Auditoria LGPD e Governança.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Registro de evento na trilha de auditoria do sistema."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    farm_id: Optional[str] = None
    action: str = Field(..., description="Ação auditada (ex: UPDATE_FARM_ALERT_THRESHOLDS, EXPORT_PDF_REPORT)")
    entity_type: str = Field(..., description="Tipo da entidade afetada (farm, report, telemetry)")
    entity_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadados da alteração")
    ip_address: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: Optional[str] = None
