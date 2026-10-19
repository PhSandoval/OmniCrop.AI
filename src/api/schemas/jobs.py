"""
Schemas Pydantic v2 para Background Jobs e Telemetria de Cache - OmniCrop AI.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BatchKpisRequest(BaseModel):
    """Payload para solicitação de cálculo de balanço hídrico em lote."""
    farm_ids: List[str] = Field(..., min_length=1, description="Lista de IDs de talhões ou fazendas a processar")
    crop_id: str = Field(default="sugarcane", description="Identificador da cultura agrícola avaliada")
    lat: float = Field(default=-21.17, description="Latitude média da região de monitoramento")
    lon: float = Field(default=-47.81, description="Longitude média da região de monitoramento")


class BatchReportsRequest(BaseModel):
    """Payload para solicitação de geração de relatórios técnicos em lote."""
    farm_ids: List[str] = Field(..., min_length=1, description="Lista de IDs de talhões ou fazendas")
    crop_id: str = Field(default="sugarcane", description="Identificador da cultura")


class BatchRetrainRequest(BaseModel):
    """Payload para auditoria de retreino e calibração de modelos em background."""
    crops: List[str] = Field(
        default=["sugarcane", "soybean", "corn", "coffee", "cotton"],
        description="Culturas alvo para validação de métricas de calibração",
    )


class JobSubmissionResponse(BaseModel):
    """Confirmação de recebimento e enfileiramento do job assíncrono."""
    job_id: str = Field(..., description="Identificador único (UUID) do job")
    job_type: str = Field(..., description="Tipo de tarefa submetida")
    status: str = Field(..., description="Status de processamento na fila")
    message: str = Field(..., description="Mensagem de aceite")
    created_at: str = Field(..., description="Timestamp ISO de criação")


class JobStatusResponse(BaseModel):
    """Detalhes completos de execução, progresso e resultados de um background job."""
    job_id: str = Field(..., description="UUID do job")
    job_type: str = Field(..., description="Tipo da tarefa")
    status: str = Field(..., description="Status atual (pending, running, completed, failed, cancelled)")
    progress: float = Field(..., description="Percentual de conclusão (0 a 100%)")
    message: str = Field(..., description="Mensagem de progresso ou conclusão")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros de entrada da tarefa")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Resultado final da tarefa quando concluída")
    error: Optional[str] = Field(default=None, description="Mensagem de erro caso a tarefa tenha falhado")
    created_at: str = Field(..., description="Data/hora de submissão")
    updated_at: str = Field(..., description="Data/hora da última atualização")
    completed_at: Optional[str] = Field(default=None, description="Data/hora de conclusão")


class JobListResponse(BaseModel):
    """Lista de jobs com contagem total."""
    jobs: List[JobStatusResponse] = Field(..., description="Lista de registros de jobs")
    total: int = Field(..., description="Total de jobs retornados")


class CacheStatsResponse(BaseModel):
    """Estatísticas operacionais e telemetria do sistema de cache centralizado."""
    backend: str = Field(..., description="Tipo do backend ativo ('redis' ou 'in_memory')")
    connected: bool = Field(..., description="Status da conectividade")
    hits: int = Field(..., description="Número de acessos atendidos pelo cache (hits)")
    misses: int = Field(..., description="Número de acessos que precisaram consultar a fonte original (misses)")
    total_requests: int = Field(..., description="Total de requisições de consulta")
    hit_ratio_pct: float = Field(..., description="Taxa de acerto do cache em porcentagem")
    keys_count: int = Field(..., description="Total de chaves ativas no cache")


class CacheClearResponse(BaseModel):
    """Confirmação de limpeza do cache."""
    status: str = Field(default="ok", description="Status da operação")
    message: str = Field(..., description="Mensagem descritiva")
