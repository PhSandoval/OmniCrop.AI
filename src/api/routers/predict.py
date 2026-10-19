"""
Endpoints para Inferência de NDVI e Explicabilidade XAI.
"""
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from src.api.schemas.predict import (
    DSSDecision,
    PredictNDVIRequest,
    PredictNDVIResponse,
    XAIWaterfallExplanation,
)
from src.core.crop_config import normalize_crop_id, get_crop_parameters
from src.models.predict import (
    calcular_dss,
    explain_prediction_delta,
    get_prediction,
)

router = APIRouter()


@router.post(
    "/predict/ndvi",
    response_model=PredictNDVIResponse,
    status_code=status.HTTP_200_OK,
    summary="Predição de Vigor Vegetativo (NDVI) com XAI e DSS",
    description=(
        "Executa a inferência do satélite virtual baseada no histórico termohídrico da cultura, "
        "com suporte a decomposição marginal XAI Waterfall e recomendações do Sistema de Suporte à Decisão (DSS)."
    ),
)
def predict_ndvi(req: PredictNDVIRequest) -> PredictNDVIResponse:
    canon_crop_id = normalize_crop_id(req.crop_id)
    crop_params = get_crop_parameters(canon_crop_id)

    payload_sim: Dict[str, float] = {
        "chuva_acumulada_30d": float(req.chuva_acumulada_30d),
        "chuva_acumulada_60d": float(req.chuva_acumulada_60d),
        "chuva_acumulada_90d": float(req.chuva_acumulada_90d),
        "GDA_mensal": float(req.GDA_mensal),
    }

    pred_res = get_prediction(payload_sim, crop_id=canon_crop_id)
    if not pred_res:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao executar o modelo preditivo para a cultura especificada.",
        )

    # 1. Resolução da Explicabilidade XAI (Decomposição Marginal Waterfall)
    xai_data: XAIWaterfallExplanation | None = None
    if req.include_xai:
        payload_base: Dict[str, float] = {
            "chuva_acumulada_30d": float(
                req.baseline_chuva_acumulada_30d
                if req.baseline_chuva_acumulada_30d is not None
                else max(0.0, req.chuva_acumulada_30d - 15.0)
            ),
            "chuva_acumulada_60d": float(
                req.baseline_chuva_acumulada_60d
                if req.baseline_chuva_acumulada_60d is not None
                else req.chuva_acumulada_60d
            ),
            "chuva_acumulada_90d": float(
                req.baseline_chuva_acumulada_90d
                if req.baseline_chuva_acumulada_90d is not None
                else req.chuva_acumulada_90d
            ),
            "GDA_mensal": float(
                req.baseline_GDA_mensal
                if req.baseline_GDA_mensal is not None
                else max(0.0, req.GDA_mensal - 20.0)
            ),
        }
        raw_xai = explain_prediction_delta(
            payload_base=payload_base,
            payload_sim=payload_sim,
            crop_id=canon_crop_id,
        )
        xai_data = XAIWaterfallExplanation(
            pred_base=raw_xai.get("pred_base", 0.0),
            pred_sim=raw_xai.get("pred_sim", 0.0),
            total_delta=raw_xai.get("total_delta", 0.0),
            contributions=raw_xai.get("contributions", {}),
            top_driver=raw_xai.get("top_driver", "N/A"),
            narrativa=raw_xai.get("narrativa", ""),
        )

    # 2. Resolução do Sistema de Suporte à Decisão (DSS)
    dss_data: DSSDecision | None = None
    if req.scenario_name or req.mes_atual is not None:
        mes = req.mes_atual if req.mes_atual is not None else datetime.now().month
        dss_raw = calcular_dss(
            mes_atual=mes,
            ndvi_atual=pred_res.get("ndvi_previsto", 0.5),
            ndvi_projetado=pred_res.get("ndvi_previsto", 0.5),
            cenario=req.scenario_name or "",
            chuva_projetada=req.chuva_acumulada_30d,
            gda_projetado=req.GDA_mensal,
        )
        dss_data = DSSDecision(
            status_title=dss_raw.get("status_title", ""),
            mensagem_recomendacao=dss_raw.get("mensagem_recomendacao", ""),
        )

    return PredictNDVIResponse(
        crop_id=canon_crop_id,
        crop_name=crop_params.name,
        ndvi_previsto=pred_res.get("ndvi_previsto", 0.0),
        status_vigor=pred_res.get("status_vigor", "Indeterminado"),
        confiabilidade_modelo=pred_res.get("confiabilidade_modelo", "Padrão"),
        fase_fenologica=pred_res.get("fase_fenologica", "Desenvolvimento"),
        fatores_de_risco_identificados=pred_res.get("fatores_de_risco_identificados", []),
        dss=dss_data,
        xai=xai_data,
    )
