"""
Endpoints para Auditoria de Data Drift e Monitoramento de MLOps.
"""
from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas.mlops import (
    DataDriftStatusResponse,
    FeatureDriftDetail,
)
from src.mlops.data_drift import detect_data_drift

router = APIRouter()


@router.get(
    "/mlops/drift-status",
    response_model=DataDriftStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Auditoria de Data Drift e Estabilidade Populacional",
    description=(
        "Executa a verificação estatística de desvio de distribuição (Population Stability Index e Kolmogorov-Smirnov) "
        "comparando as variáveis meteorológicas da esteira ativa contra a população de calibração histórica."
    ),
)
def get_drift_status(
    psi_threshold: float = Query(
        default=0.20,
        ge=0.01,
        le=1.0,
        description="Limiar de PSI para considerar deriva severa da distribuição",
    ),
    p_value_threshold: float = Query(
        default=0.05,
        ge=0.001,
        le=0.5,
        description="P-valor crítico do teste Kolmogorov-Smirnov",
    ),
    auto_alert: bool = Query(
        default=False,
        description="Se verdadeiro, despacha alertas multicanal caso deriva crítica seja detectada",
    ),
) -> DataDriftStatusResponse:
    try:
        report = detect_data_drift(
            current_df=None,
            baseline_df=None,
            auto_alert=auto_alert,
            psi_threshold=psi_threshold,
            p_value_threshold=p_value_threshold,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao executar auditoria de Data Drift: {e}",
        )

    metrics_mapped = {}
    for k, v in report.metrics.items():
        metrics_mapped[k] = FeatureDriftDetail(
            feature_name=v.feature_name,
            psi=round(v.psi, 4),
            ks_p_value=round(v.p_value, 4),
            drift_detected=v.drift_detected,
            severity=v.severity,
            baseline_mean=round(v.baseline_mean, 3),
            current_mean=round(v.current_mean, 3),
            baseline_std=round(v.baseline_std, 3),
            current_std=round(v.current_std, 3),
        )

    if report.dataset_drift_detected:
        system_status = "DRIFT_DETECTED"
    elif report.drifted_features_count > 0:
        system_status = "WARNING"
    else:
        system_status = "HEALTHY"

    return DataDriftStatusResponse(
        status=system_status,
        timestamp=report.timestamp,
        total_features_evaluated=report.total_features_evaluated,
        drifted_features_count=report.drifted_features_count,
        dataset_drift_detected=report.dataset_drift_detected,
        alert_dispatched=report.alert_dispatched,
        summary=report.summary,
        metrics=metrics_mapped,
    )
