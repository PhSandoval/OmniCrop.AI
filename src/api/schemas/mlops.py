"""
Schemas Pydantic v2 para Auditoria de Data Drift e Monitoramento de MLOps.
"""
from typing import Dict
from pydantic import BaseModel, Field


class FeatureDriftDetail(BaseModel):
    """Diagnóstico estatístico detalhado de uma feature climática/biofísica."""
    feature_name: str
    psi: float = Field(..., description="Population Stability Index")
    ks_p_value: float = Field(..., description="P-valor do teste bicaudal Kolmogorov-Smirnov")
    drift_detected: bool = Field(..., description="Se a feature sofreu desvio estatístico relevante")
    severity: str = Field(..., description="Classificação de severidade: 'ESTÁVEL', 'MODERADO' ou 'CRÍTICO'")
    baseline_mean: float
    current_mean: float
    baseline_std: float
    current_std: float


class DataDriftStatusResponse(BaseModel):
    """Relatório consolidado de auditoria de Data Drift do pipeline."""
    status: str = Field(..., description="Status geral da esteira ('HEALTHY', 'WARNING' ou 'DRIFT_DETECTED')")
    timestamp: str = Field(..., description="Timestamp ISO 8601 da auditoria")
    total_features_evaluated: int
    drifted_features_count: int
    dataset_drift_detected: bool
    alert_dispatched: bool
    summary: str
    metrics: Dict[str, FeatureDriftDetail]
