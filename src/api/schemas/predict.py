"""
Schemas Pydantic v2 para Inferência de NDVI e Explicabilidade XAI.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PredictNDVIRequest(BaseModel):
    """Payload de entrada para inferência do modelo biofísico de NDVI."""
    crop_id: str = Field(
        default="sugarcane",
        description="Identificador da cultura ('sugarcane', 'soybean', 'corn', 'coffee', 'pasture')",
    )
    chuva_acumulada_30d: float = Field(
        ...,
        ge=0.0,
        description="Chuva acumulada nos últimos 30 dias (mm)",
    )
    chuva_acumulada_60d: float = Field(
        ...,
        ge=0.0,
        description="Chuva acumulada nos últimos 60 dias (mm)",
    )
    chuva_acumulada_90d: float = Field(
        ...,
        ge=0.0,
        description="Chuva acumulada nos últimos 90 dias (mm)",
    )
    GDA_mensal: float = Field(
        ...,
        ge=0.0,
        description="Graus-Dia Acumulados mensais acima da temperatura-base da cultura",
    )
    include_xai: bool = Field(
        default=True,
        description="Se verdadeiro, calcula a decomposição marginal XAI Waterfall do impacto de cada feature",
    )
    scenario_name: Optional[str] = Field(
        default="",
        description="Cenário simulado para o DSS (ex: 'Irrigação +20mm', 'Maturador', 'Colheita', 'Plantio', 'Adubação')",
    )
    mes_atual: Optional[int] = Field(
        default=None,
        ge=1,
        le=12,
        description="Mês de referência (1-12) para análise fenológica e regras sazonais do DSS",
    )
    baseline_chuva_acumulada_30d: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Baseline de chuva 30d para comparação no XAI (se não informado, deriva do valor atual)",
    )
    baseline_chuva_acumulada_60d: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Baseline de chuva 60d para comparação no XAI",
    )
    baseline_chuva_acumulada_90d: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Baseline de chuva 90d para comparação no XAI",
    )
    baseline_GDA_mensal: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Baseline de GDA para comparação no XAI",
    )


class XAIWaterfallExplanation(BaseModel):
    """Decomposição matemática da variação marginal das features no índice NDVI."""
    pred_base: float = Field(..., description="NDVI estimado para o cenário base")
    pred_sim: float = Field(..., description="NDVI estimado para o cenário simulado")
    total_delta: float = Field(..., description="Variação total de NDVI (pred_sim - pred_base)")
    contributions: Dict[str, float] = Field(..., description="Contribuição marginal de cada variável climática")
    top_driver: str = Field(..., description="Variável climática de maior impacto no resultado")
    narrativa: str = Field(..., description="Síntese explicativa em linguagem agronômica natural")


class DSSDecision(BaseModel):
    """Recomendação agronômica gerada pelo Sistema de Suporte à Decisão (DSS)."""
    status_title: str = Field(..., description="Título resumido do status operacional (ex: 🟢 Aplicação Ideal)")
    mensagem_recomendacao: str = Field(..., description="Parecer operacional detalhado para manejo de campo")


class PredictNDVIResponse(BaseModel):
    """Resposta consolidada de predição do satélite virtual com XAI e DSS."""
    crop_id: str = Field(..., description="Código canônico da cultura")
    crop_name: str = Field(..., description="Nome comercial da cultura")
    ndvi_previsto: float = Field(..., description="Índice NDVI estimado (0.0 a 1.0)")
    status_vigor: str = Field(..., description="Classificação do vigor vegetativo")
    confiabilidade_modelo: str = Field(..., description="Grau de confiança estatística do regressor")
    fase_fenologica: str = Field(..., description="Fase fenológica ativa da cultura")
    fatores_de_risco_identificados: List[str] = Field(
        default_factory=list,
        description="Alertas agroclimáticos identificados pela inferência",
    )
    dss: Optional[DSSDecision] = Field(
        default=None,
        description="Recomendação de tomada de decisão quando cenário ou mês for informado",
    )
    xai: Optional[XAIWaterfallExplanation] = Field(
        default=None,
        description="Decomposição XAI Waterfall da contribuição de cada variável climática",
    )
